# Retry Strategies

## Overview

When a consumer fails to process a message, you have three options: skip it,
block on it forever, or retry it intelligently. Skipping loses data. Blocking
stalls the pipeline. Intelligent retry is the only production-viable path.

This lab covers the three retry strategies you will use in practice, when each
is appropriate, and how they compose with the DLQ pattern from Lab 05.

- **Immediate retry** — retry on the spot, N times, with no delay
- **Exponential backoff retry** — retry with increasing delays between attempts
- **Retry topic** — publish to a dedicated retry topic and re-consume later

Each strategy suits a different class of failure. By the end of the lab you will
be able to look at an exception and know which strategy belongs.

---

## Background: Classifying Failures

Before choosing a retry strategy, classify the failure. The wrong strategy for
the failure class wastes time at best and makes things worse at worst.

| Failure class              | Examples                                                                    | Right strategy                   |
| -------------------------- | --------------------------------------------------------------------------- | -------------------------------- |
| Transient / infrastructure | Network blip, broker briefly unavailable, connection timeout                | Immediate retry with small limit |
| Recoverable with time      | Downstream service overloaded, rate limit hit, DB connection pool exhausted | Exponential backoff              |
| Requires external change   | Dependent service deploying new version, data migration in progress         | Retry topic with long delay      |
| Permanent / logic error    | Schema validation failure, unknown message type, corrupt payload            | No retry — DLQ immediately       |

Retrying a permanent failure is pure waste. Every retry attempt consumes
resources, burns through your retry budget, and delays the message reaching the
DLQ where it can actually be investigated. The first thing your error handler
should do is classify the exception.

---

## Part 1 — Setup

### 1.1 Create the lab topics

```bash
rpk topic create pipeline.events \
  --partitions 3 --replicas 1

rpk topic create pipeline.events.retry \
  --partitions 3 --replicas 1 \
  --topic-config retention.ms=3600000   # 1 hour — retries should not sit forever

rpk topic create pipeline.events.dlq \
  --partitions 3 --replicas 1 \
  --topic-config retention.ms=604800000 # 7 days
```

### 1.2 Create a shared producer

Create `producer.py` — produces a controlled mix of events that will succeed,
fail transiently, fail with backoff, and fail permanently:

```python
#!/usr/bin/env python3
"""Lab 09 producer — emits events with embedded failure instructions."""

import json
import uuid
import time
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC     = "pipeline.events"


def event(name: str, version: str, failure_mode: str = "none",
          fail_count: int = 0) -> dict:
    return {
        "id":           str(uuid.uuid4()),
        "name":         name,
        "version":      version,
        "failure_mode": failure_mode,   # none | transient | backoff | permanent
        "fail_count":   fail_count,     # how many times to fail before succeeding
    }


def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )

    messages = [
        event("service-a", "1.0.0"),                          # succeeds first try
        event("service-b", "1.0.0", "transient",   2),        # fails twice, then ok
        event("service-c", "1.0.0", "backoff",     3),        # fails three times
        event("service-d", "1.0.0", "permanent"),             # always fails → DLQ
        event("service-e", "1.0.0"),                          # succeeds first try
        event("service-f", "1.0.0", "transient",   1),        # fails once, then ok
        event("service-g", "1.0.0", "retry_topic", 2),        # needs retry topic
        event("service-h", "1.0.0", "permanent"),             # always fails → DLQ
    ]

    for msg in messages:
        producer.send(TOPIC, value=msg)
        print(f"  SENT  {msg['name']} {msg['version']}  "
              f"failure_mode={msg['failure_mode']}")
        time.sleep(0.05)

    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()
```

---

## Part 2 — Immediate Retry

Immediate retry is the simplest strategy. On failure, retry the operation up to
N times in a tight loop with no sleep. Use it when the failure is almost
certainly a transient network blip that resolves in milliseconds.

Do not use it when:

- The failure is a downstream service under load — hammering it makes things
  worse
- N is large — it blocks the consumer thread and stalls partition processing
- You need to maintain message order across partitions

A good rule of thumb: immediate retry with N ≤ 3 for infrastructure-level errors
(connection reset, timeout). Anything that needs more than 3 immediate retries
is not a transient blip — use backoff instead.

Create `consumer_immediate_retry.py`:

```python
#!/usr/bin/env python3
"""
Lab 09 — Strategy 1: Immediate retry.

Retries the processing function up to MAX_RETRIES times with no delay.
Appropriate for: connection resets, brief network blips.
Not appropriate for: overloaded downstream services, logic errors.
"""

import json
import datetime
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP  = "localhost:9092"
TOPIC      = "pipeline.events"
DLQ        = "pipeline.events.dlq"
GROUP      = "immediate-retry-consumer"
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Simulated processing — raises based on the event's failure_mode field
# ---------------------------------------------------------------------------

class TransientError(Exception):
    """Temporary infrastructure failure — safe to retry immediately."""

class PermanentError(Exception):
    """Logic or data error — retrying will never help."""


_attempt_counts: dict[str, int] = {}

def process(event: dict) -> None:
    """
    Simulates processing with controllable failure modes.
    In a real consumer this would call a database, API, or downstream service.
    """
    event_id = event["id"]
    mode     = event.get("failure_mode", "none")
    max_fail = event.get("fail_count", 0)

    if mode == "permanent":
        raise PermanentError(f"Invalid payload structure in {event['name']}")

    if mode == "transient":
        _attempt_counts[event_id] = _attempt_counts.get(event_id, 0) + 1
        if _attempt_counts[event_id] <= max_fail:
            raise TransientError(
                f"Connection reset on attempt {_attempt_counts[event_id]}"
            )

    print(f"    ✓  Processed: {event['name']} {event['version']}")


# ---------------------------------------------------------------------------
# DLQ helper
# ---------------------------------------------------------------------------

def send_to_dlq(producer, record, error: Exception, attempts: int) -> None:
    headers = [
        ("dlq.original.topic",   TOPIC.encode()),
        ("dlq.error.type",       type(error).__name__.encode()),
        ("dlq.error.message",    str(error)[:200].encode()),
        ("dlq.retry.strategy",   b"immediate"),
        ("dlq.attempts",         str(attempts).encode()),
        ("dlq.timestamp",        datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(DLQ, key=record.key, value=record.value, headers=headers).get(timeout=5)
    print(f"    ✗  → DLQ after {attempts} attempt(s): {error}")


# ---------------------------------------------------------------------------
# Consumer loop
# ---------------------------------------------------------------------------

def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda b: json.loads(b.decode()),
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    print(f"Immediate retry consumer  (max retries={MAX_RETRIES})\n")

    for record in consumer:
        event    = record.value
        attempts = 0
        success  = False

        print(f"  MSG  {event['name']} {event['version']}  "
              f"mode={event['failure_mode']}")

        # Non-retryable: send straight to DLQ, never waste a retry attempt
        if event.get("failure_mode") == "permanent":
            try:
                process(event)
            except PermanentError as e:
                send_to_dlq(producer, record, e, 1)
            consumer.commit()
            continue

        # Retryable: attempt up to MAX_RETRIES times
        while attempts <= MAX_RETRIES and not success:
            try:
                process(event)
                success = True
            except TransientError as e:
                attempts += 1
                if attempts > MAX_RETRIES:
                    send_to_dlq(producer, record, e, attempts)
                else:
                    print(f"    ↻  TransientError, retrying immediately "
                          f"({attempts}/{MAX_RETRIES}): {e}")
            except Exception as e:
                # Unexpected error — treat as permanent
                send_to_dlq(producer, record, e, attempts + 1)
                break

        consumer.commit()

    consumer.close()
    producer.close()


if __name__ == "__main__":
    main()
```

Run the producer, then the consumer:

```bash
python producer.py
python consumer_immediate_retry.py
```

Observe: transient failures retry immediately and succeed. Permanent failures go
straight to the DLQ without burning retry attempts. The `service-b` and
`service-f` events succeed after 2 and 1 retries respectively. `service-d` and
`service-h` land in the DLQ after a single attempt.

---

## Part 3 — Exponential Backoff

Exponential backoff introduces a delay between retry attempts that grows with
each failure. The formula is:

```
delay = base_delay * (2 ^ attempt) + jitter
```

The jitter term — a small random value — is important. Without it, multiple
consumers that all failed at the same moment will all retry at the same moment,
creating a thundering herd that re-fails the downstream service they were trying
to reach.

Backoff is appropriate when the failure is caused by a service under load or a
resource constraint that needs time to recover. You are giving the system
breathing room rather than hammering it harder.

Create `consumer_backoff.py`:

```python
#!/usr/bin/env python3
"""
Lab 09 — Strategy 2: Exponential backoff with jitter.

Delays grow as: base * 2^attempt + random(0, jitter_ms/1000)
Appropriate for: overloaded downstream services, rate limit errors,
                 resource pool exhaustion.
"""

import json
import time
import random
import datetime
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP    = "localhost:9092"
TOPIC        = "pipeline.events"
DLQ          = "pipeline.events.dlq"
GROUP        = "backoff-consumer"
MAX_RETRIES  = 4
BASE_DELAY   = 0.5    # seconds — base of the exponential
MAX_DELAY    = 30.0   # seconds — cap so we don't wait forever
JITTER_MS    = 500    # milliseconds of random jitter added to each delay


class BackoffError(Exception):
    """Failure that benefits from waiting before retry."""

class PermanentError(Exception):
    pass


_attempt_counts: dict[str, int] = {}

def process(event: dict) -> None:
    event_id = event["id"]
    mode     = event.get("failure_mode", "none")
    max_fail = event.get("fail_count", 0)

    if mode == "permanent":
        raise PermanentError(f"Unrecognised event type in {event['name']}")

    if mode in ("backoff", "transient"):
        _attempt_counts[event_id] = _attempt_counts.get(event_id, 0) + 1
        if _attempt_counts[event_id] <= max_fail:
            raise BackoffError(
                f"Downstream service unavailable (attempt {_attempt_counts[event_id]})"
            )

    print(f"    ✓  Processed: {event['name']} {event['version']}")


def backoff_delay(attempt: int) -> float:
    """Return the sleep duration for a given attempt number (0-indexed)."""
    delay = BASE_DELAY * (2 ** attempt)
    delay = min(delay, MAX_DELAY)
    delay += random.uniform(0, JITTER_MS / 1000)
    return delay


def send_to_dlq(producer, record, error: Exception, attempts: int) -> None:
    headers = [
        ("dlq.original.topic",  TOPIC.encode()),
        ("dlq.error.type",      type(error).__name__.encode()),
        ("dlq.error.message",   str(error)[:200].encode()),
        ("dlq.retry.strategy",  b"exponential_backoff"),
        ("dlq.attempts",        str(attempts).encode()),
        ("dlq.timestamp",       datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(DLQ, key=record.key, value=record.value, headers=headers).get(timeout=5)
    print(f"    ✗  → DLQ after {attempts} attempt(s): {error}")


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda b: json.loads(b.decode()),
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    print(f"Backoff consumer  "
          f"(max_retries={MAX_RETRIES}, base={BASE_DELAY}s, max={MAX_DELAY}s)\n")

    for record in consumer:
        event    = record.value
        attempt  = 0
        success  = False

        print(f"  MSG  {event['name']} {event['version']}  "
              f"mode={event['failure_mode']}")

        if event.get("failure_mode") == "permanent":
            try:
                process(event)
            except PermanentError as e:
                send_to_dlq(producer, record, e, 1)
            consumer.commit()
            continue

        while attempt <= MAX_RETRIES and not success:
            try:
                process(event)
                success = True
            except BackoffError as e:
                attempt += 1
                if attempt > MAX_RETRIES:
                    send_to_dlq(producer, record, e, attempt)
                else:
                    delay = backoff_delay(attempt - 1)
                    print(f"    ↻  BackoffError, sleeping {delay:.2f}s "
                          f"(attempt {attempt}/{MAX_RETRIES}): {e}")
                    time.sleep(delay)
            except Exception as e:
                send_to_dlq(producer, record, e, attempt + 1)
                break

        consumer.commit()

    consumer.close()
    producer.close()


if __name__ == "__main__":
    main()
```

```bash
python consumer_backoff.py
```

Watch the delay grow between retries for `service-c`. Each attempt takes roughly
twice as long as the previous one, plus a small random jitter. Measure the
timing:

```bash
python consumer_backoff.py 2>&1 | grep -E "MSG|sleeping|Processed|DLQ" | \
  awk '{print strftime("%H:%M:%S"), $0}'
```

---

## Part 4 — Retry Topic

Immediate retry and backoff both block the consumer thread while retrying. For
failures that need a long wait — minutes or hours, not seconds — blocking is
unacceptable. The consumer falls behind, consumer lag climbs, and the pipeline
stalls.

The retry topic pattern solves this by publishing the failed message to a
separate topic with a delay baked in. The original consumer is unblocked
immediately. A dedicated retry consumer reads the retry topic and re-attempts
processing after the delay has elapsed.

```
pipeline.events ──► consumer ──► (failure) ──► pipeline.events.retry
                                                        │
                                              (wait N seconds/minutes)
                                                        │
                                              retry consumer re-attempts
                                                        │
                                            success ──► done
                                            failure ──► pipeline.events.dlq
```

The retry topic approach is right when:

- The delay needed is longer than you are willing to block a consumer thread (>
  ~30 seconds)
- The downstream dependency is known to be recovering and you want to try again
  in several minutes
- You want retry processing to be independently scalable and observable from the
  primary consumer

Create `consumer_retry_topic.py`:

```python
#!/usr/bin/env python3
"""
Lab 09 — Strategy 3: Retry topic.

On failure, publishes to pipeline.events.retry with metadata headers.
A separate retry consumer re-attempts after a configurable delay.
The primary consumer is never blocked.
"""

import json
import datetime
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP   = "localhost:9092"
TOPIC       = "pipeline.events"
RETRY_TOPIC = "pipeline.events.retry"
DLQ         = "pipeline.events.dlq"
GROUP       = "retry-topic-consumer"
MAX_RETRIES = 3


class RetryableError(Exception):
    """Failure that warrants a delayed re-attempt via the retry topic."""

class PermanentError(Exception):
    pass


_attempt_counts: dict[str, int] = {}

def process(event: dict) -> None:
    event_id = event["id"]
    mode     = event.get("failure_mode", "none")
    max_fail = event.get("fail_count", 0)

    if mode == "permanent":
        raise PermanentError(f"Malformed payload in {event['name']}")

    if mode in ("retry_topic", "backoff", "transient"):
        _attempt_counts[event_id] = _attempt_counts.get(event_id, 0) + 1
        if _attempt_counts[event_id] <= max_fail:
            raise RetryableError(
                f"Downstream service not ready (attempt {_attempt_counts[event_id]})"
            )

    print(f"    ✓  Processed: {event['name']} {event['version']}")


def route_to_retry(producer, record, error: Exception,
                   current_attempt: int) -> None:
    """Publish to the retry topic with attempt count in headers."""
    headers = [
        ("retry.original.topic",  TOPIC.encode()),
        ("retry.attempt",         str(current_attempt).encode()),
        ("retry.max_attempts",    str(MAX_RETRIES).encode()),
        ("retry.error.type",      type(error).__name__.encode()),
        ("retry.error.message",   str(error)[:200].encode()),
        ("retry.queued_at",       datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(
        RETRY_TOPIC,
        key=record.key,
        value=record.value,
        headers=headers,
    ).get(timeout=5)
    print(f"    ↻  → retry topic (attempt {current_attempt}/{MAX_RETRIES}): {error}")


def route_to_dlq(producer, record, error: Exception, attempts: int) -> None:
    headers = [
        ("dlq.original.topic",  TOPIC.encode()),
        ("dlq.error.type",      type(error).__name__.encode()),
        ("dlq.error.message",   str(error)[:200].encode()),
        ("dlq.retry.strategy",  b"retry_topic"),
        ("dlq.attempts",        str(attempts).encode()),
        ("dlq.timestamp",       datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(DLQ, key=record.key, value=record.value, headers=headers).get(timeout=5)
    print(f"    ✗  → DLQ after {attempts} attempt(s): {error}")


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda b: json.loads(b.decode()),
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    print(f"Retry-topic consumer  (max_retries={MAX_RETRIES})\n")

    for record in consumer:
        event = record.value
        print(f"  MSG  {event['name']} {event['version']}  "
              f"mode={event['failure_mode']}")

        try:
            process(event)
        except PermanentError as e:
            route_to_dlq(producer, record, e, 1)
        except RetryableError as e:
            # Read current attempt count from headers (0 if coming from main topic)
            headers = {k: v.decode() for k, v in record.headers}
            attempt = int(headers.get("retry.attempt", "0")) + 1

            if attempt >= MAX_RETRIES:
                route_to_dlq(producer, record, e, attempt)
            else:
                route_to_retry(producer, record, e, attempt)

        consumer.commit()

    consumer.close()
    producer.close()


if __name__ == "__main__":
    main()
```

Now create the retry consumer that re-attempts with a delay:

```python
#!/usr/bin/env python3
"""
Lab 09 — Retry topic consumer.

Reads from pipeline.events.retry, waits RETRY_DELAY_SECONDS,
then re-attempts. Routes back to retry topic (up to MAX_RETRIES)
or to DLQ on exhaustion.
"""

import json
import time
import datetime
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP          = "localhost:9092"
RETRY_TOPIC        = "pipeline.events.retry"
DLQ                = "pipeline.events.dlq"
GROUP              = "retry-topic-retry-consumer"
RETRY_DELAY        = 5    # seconds — use 60-300 in production
MAX_RETRIES        = 3


_attempt_counts: dict[str, int] = {}

def process(event: dict) -> None:
    """Same processing logic as the primary consumer."""
    event_id = event["id"]
    mode     = event.get("failure_mode", "none")
    max_fail = event.get("fail_count", 0)

    if mode == "permanent":
        raise ValueError(f"Permanent error in {event['name']}")

    if mode in ("retry_topic", "backoff", "transient"):
        _attempt_counts[event_id] = _attempt_counts.get(event_id, 0) + 1
        if _attempt_counts[event_id] <= max_fail:
            raise ConnectionError(
                f"Still unavailable (attempt {_attempt_counts[event_id]})"
            )

    print(f"    ✓  Processed on retry: {event['name']} {event['version']}")


def route_to_dlq(producer, record, error: Exception, attempts: int) -> None:
    headers = [
        ("dlq.original.topic",  RETRY_TOPIC.encode()),
        ("dlq.error.type",      type(error).__name__.encode()),
        ("dlq.error.message",   str(error)[:200].encode()),
        ("dlq.retry.strategy",  b"retry_topic"),
        ("dlq.attempts",        str(attempts).encode()),
        ("dlq.timestamp",       datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(DLQ, key=record.key, value=record.value, headers=headers).get(timeout=5)
    print(f"    ✗  → DLQ after {attempts} total attempt(s): {error}")


def main():
    consumer = KafkaConsumer(
        RETRY_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=10000,
        value_deserializer=lambda b: json.loads(b.decode()),
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    print(f"Retry consumer  (delay={RETRY_DELAY}s, max_retries={MAX_RETRIES})\n")

    for record in consumer:
        headers  = {k: v.decode() for k, v in record.headers}
        attempt  = int(headers.get("retry.attempt", "1"))
        event    = record.value

        print(f"  RETRY MSG  {event['name']}  attempt={attempt}/{MAX_RETRIES}  "
              f"sleeping {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)

        try:
            process(event)
        except Exception as e:
            if attempt >= MAX_RETRIES:
                route_to_dlq(producer, record, e, attempt)
            else:
                # Re-queue with incremented attempt count
                new_headers = list(record.headers)
                new_headers = [(k, v) for k, v in new_headers
                               if k != "retry.attempt"]
                new_headers.append(
                    ("retry.attempt", str(attempt + 1).encode())
                )
                producer.send(
                    RETRY_TOPIC,
                    key=record.key,
                    value=record.value,
                    headers=new_headers,
                ).get(timeout=5)
                print(f"    ↻  Re-queued for attempt {attempt + 1}/{MAX_RETRIES}")

        consumer.commit()

    consumer.close()
    producer.close()
    print("Retry consumer done.")


if __name__ == "__main__":
    main()
```

Run all three in separate terminals:

```bash
# Terminal 1 — primary consumer (routes failures to retry topic)
python consumer_retry_topic.py

# Terminal 2 — retry consumer (re-attempts after delay)
python retry_consumer.py

# Terminal 3 — produce fresh messages
python producer.py
```

---

## Part 5 — Choosing the Right Strategy

Run this decision exercise. For each scenario, decide which strategy belongs
before reading the answer.

**Scenario 1:** Your watcher consumer calls a PostgreSQL query that occasionally
times out under load. Failures are rare, usually resolve in under a second, and
timeout errors make up less than 1% of traffic.

Answer: Immediate retry (N=2 or 3). The failure resolves in milliseconds.
Backoff is overkill. The retry topic adds unnecessary infrastructure for a
sub-second transient.

**Scenario 2:** Your watcher consumer calls an external vulnerability scanning
API. The API enforces rate limits — 100 requests per minute. When the limit is
hit it returns HTTP 429.

Answer: Exponential backoff. A 429 tells you exactly why it failed and that
waiting will fix it. The delay needs to be long enough for the rate limit window
to reset, so backoff to a maximum of 60-90 seconds is appropriate.

**Scenario 3:** Your consumer triggers a deployment pipeline in an external
system. That system is undergoing a maintenance window for the next 30 minutes.

Answer: Retry topic with a long delay (e.g. RETRY_DELAY = 600 seconds). Blocking
a consumer thread for 30 minutes is unacceptable. The retry topic lets the
primary consumer continue processing other messages while the deployment
messages wait.

**Scenario 4:** Your consumer receives a message with `artifact_sha: null`.

Answer: No retry — DLQ immediately. This is a permanent error. The message will
never become valid through retrying. Every retry attempt is wasted work.

---

## Part 6 — Challenge Exercises

### Challenge A: Retry budget across strategies

Combine all three strategies in a single consumer. The consumer should:

- Try immediate retry (x2) for `TransientError`
- Escalate to backoff (x3) if immediate retries are exhausted
- Escalate to the retry topic if backoff is also exhausted
- DLQ on permanent errors without any retry

This is the production pattern: a cascade of increasingly expensive strategies,
each triggered only when the cheaper one is exhausted.

### Challenge B: Retry topic with delay enforcement

The retry consumer currently sleeps for a fixed `RETRY_DELAY`. A more robust
implementation uses the `retry.queued_at` header to calculate how much time has
actually elapsed and only sleeps the remaining duration. Implement this so the
retry consumer is correct even if it restarts partway through the delay period.

### Challenge C: Classify your own errors

Look at the EPR watcher from the main workshop. Identify three real exceptions
the watcher could throw and classify each as transient, backoff-appropriate,
retry-topic-appropriate, or permanent. Write the classification as a Python
function `classify_error(exc: Exception) -> RetryStrategy` that returns an enum
value.

---

## Cleanup

```bash
rpk topic delete pipeline.events pipeline.events.retry pipeline.events.dlq
```

---

**Duration:** ~50 minutes **Prerequisites:** Redpanda running via Docker
Compose; Python 3.10+ with `kafka-python` installed.

---

## Key Takeaways

- Classify the failure before choosing a strategy. Retrying a permanent error is
  never useful.
- Immediate retry is for sub-second transient failures. Keep N small (≤ 3).
- Exponential backoff is for overloaded downstream systems. Always add jitter.
- Retry topics are for failures that need minutes or more to resolve. They
  decouple retry timing from consumer throughput.
- All three strategies feed the same DLQ on exhaustion — the DLQ is the safety
  net underneath all of them, not a competing approach.
- The retry topic pattern pairs directly with the DLQ lab (Lab 05). The two
  together form a complete error-handling system.
