# Dead Letter Queues with Redpanda

## Overview

In production event-driven pipelines, not every message can be processed
successfully. Schema mismatches, malformed payloads, transient downstream
failures, and unhandled business-logic exceptions all cause consumers to fail on
specific messages. Without a safety net, you face a hard choice: skip the
message and lose data, or block the pipeline indefinitely retrying it.

A **Dead Letter Queue (DLQ)** is a dedicated Kafka/Redpanda topic that receives
messages a consumer cannot process after exhausting its retry budget. The main
pipeline keeps moving; bad messages land in the DLQ where they can be inspected,
fixed, and replayed — or discarded intentionally.

### What you will learn

- Why DLQs are a first-class resilience pattern in event-driven CI/CD pipelines
- How to create and configure a DLQ topic in Redpanda
- How to implement retry-then-DLQ logic in a Python consumer
- How to enrich DLQ messages with error metadata headers
- How to inspect DLQ contents with `rpk`
- How to replay fixed messages back into the main topic

---

## Background: DLQ Concepts

### The problem DLQs solve

Consider the EPR (Event Provenance Registry) pipeline from previous labs. Events
flow from producers through topic partitions to consumers that validate,
transform, and persist them. What happens when a consumer receives a
`build.finished` event whose payload has an unexpected field added by a schema
migration — or one whose `artifact_sha` field is `null` because a upstream
service had a bug?

Without a DLQ:

- The consumer throws an exception and retries forever → **pipeline stalled**
- The consumer skips the record and commits the offset → **silent data loss**

With a DLQ:

- The consumer retries N times, then publishes the bad message to `<topic>.dlq`
  with error metadata headers → **pipeline continues, no data lost, errors are
  visible and actionable**

### DLQ anatomy

```text
Producer
   │
   ▼
[epr.events]──────────Consumer──────processing OK──▶ downstream
                           │
                           │  deserialization error
                           │  schema validation failure
                           │  business logic exception
                           │  (after N retries)
                           ▼
                    [epr.events.dlq]
                           │
                           ▼
                    DLQ Inspector / Reprocessor
```

### DLQ message headers (convention)

When routing a message to the DLQ, always preserve the original payload and add
structured headers:

| Header key               | Example value                  | Purpose                         |
| ------------------------ | ------------------------------ | ------------------------------- |
| `dlq.original.topic`     | `epr.events`                   | Where the message came from     |
| `dlq.original.partition` | `0`                            | Original partition              |
| `dlq.original.offset`    | `1042`                         | Original offset for tracing     |
| `dlq.error.type`         | `SchemaValidationError`        | Exception class name            |
| `dlq.error.message`      | `field 'artifact_sha' is null` | Human-readable reason           |
| `dlq.retry.count`        | `3`                            | How many retries were attempted |
| `dlq.timestamp`          | `2025-09-01T14:32:00Z`         | When it was DLQ'd               |
| `dlq.consumer.group`     | `epr-validator-v1`             | Which consumer group failed     |

---

## Part 1 — Environment Setup

### 1.1 Verify Redpanda is running

```bash
docker compose ps

docker exec -it redpanda \
    rpk cluster info
```

You should see your single-node Redpanda cluster responding.

### 1.2 Create the lab topics

```bash
# Main event topic (3 partitions, replication factor 1 for local dev)
docker exec -it redpanda \
    rpk topic create epr.events \
    --partitions 3 \
    --replicas 1

# Dead letter queue topic
# Tip: match partition count to the source topic so you can correlate
docker exec -it redpanda \
    rpk topic create epr.events.dlq \
        --partitions 3 \
        --replicas 1 \
        --topic-config retention.ms=604800000  # 7 days — DLQs need longer retention

# Verify
docker exec -it redpanda \
    rpk topic list
```

> **Design note:** DLQ topics should have _longer_ retention than their source
> topics. The whole point is to give operators time to investigate and
> reprocess. Seven days is a reasonable minimum; 30 days is common for
> compliance-sensitive pipelines.

### 1.3 Install Python dependencies

```bash
python3 -m venv .venv/instegrations
source .venv/integrations/bin/activate
```

```bash
pip install kafka-python-ng jsonschema
```

---

## Part 2 — Producing Mixed Good/Bad Events

Create a producer that intentionally emits a mix of valid and invalid events to
simulate real-world conditions.

### 2.1 Create `producer.py`

```python
#!/usr/bin/env python3
"""
Lab 05 producer — emits a mix of valid and deliberately broken EPR events.
"""

import json
import time
import uuid
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC = "epr.events"

VALID_EVENTS = [
    {
        "id": str(uuid.uuid4()),
        "type": "build.finished",
        "artifact_sha": "sha256:abc123def456",
        "repo": "github.com/acme/service-a",
        "status": "success",
    },
    {
        "id": str(uuid.uuid4()),
        "type": "test.passed",
        "artifact_sha": "sha256:deadbeef0000",
        "repo": "github.com/acme/service-b",
        "status": "success",
    },
]

BROKEN_EVENTS = [
    # Missing required field: artifact_sha
    {
        "id": str(uuid.uuid4()),
        "type": "build.finished",
        "repo": "github.com/acme/service-c",
        "status": "success",
    },
    # artifact_sha is null
    {
        "id": str(uuid.uuid4()),
        "type": "test.passed",
        "artifact_sha": None,
        "repo": "github.com/acme/service-d",
        "status": "success",
    },
    # Completely malformed — not valid JSON structure for an EPR event
    "THIS IS NOT VALID JSON AT ALL",
    # Unknown event type
    {
        "id": str(uuid.uuid4()),
        "type": "unknown.event.type",
        "artifact_sha": "sha256:1234",
        "repo": "github.com/acme/service-e",
        "status": "success",
    },
]

def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )

    print(f"Producing to topic: {TOPIC}")

    # Produce a batch: 2 good, 1 bad, 2 good, 3 bad, 1 good
    sequence = [
        VALID_EVENTS[0],
        VALID_EVENTS[1],
        BROKEN_EVENTS[0],   # missing artifact_sha
        VALID_EVENTS[0],
        VALID_EVENTS[1],
        BROKEN_EVENTS[1],   # null artifact_sha
        BROKEN_EVENTS[2],   # malformed string
        BROKEN_EVENTS[3],   # unknown type
        VALID_EVENTS[0],
    ]

    for i, event in enumerate(sequence):
        key = f"event-{i}"
        try:
            future = producer.send(TOPIC, key=key, value=event)
            meta = future.get(timeout=5)
            print(f"  [{i}] Sent to {meta.topic}:{meta.partition}@{meta.offset} — {str(event)[:60]}...")
        except Exception as e:
            print(f"  [{i}] Producer error: {e}")
        time.sleep(0.1)

    producer.flush()
    producer.close()
    print("Done.")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python producer.py
```

---

## Part 3 — Consumer with DLQ Logic

This is the core of the lab. You will implement a consumer that:

1. Deserializes and validates each message
2. Retries transient failures up to `MAX_RETRIES` times
3. Routes unrecoverable messages to the DLQ with full error metadata in headers

### 3.1 Create `consumer_with_dlq.py`

```python
#!/usr/bin/env python3
"""
Lab 05 consumer — processes EPR events with retry-then-DLQ error handling.
"""

import json
import time
import datetime
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

BOOTSTRAP = "localhost:9092"
SOURCE_TOPIC = "epr.events"
DLQ_TOPIC = "epr.events.dlq"
CONSUMER_GROUP = "epr-validator-v1"
MAX_RETRIES = 3

KNOWN_EVENT_TYPES = {"build.finished", "test.passed", "deploy.started", "deploy.finished"}


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

class SchemaValidationError(Exception):
    pass

class UnknownEventTypeError(Exception):
    pass

def validate_event(event: dict) -> None:
    """
    Validate an EPR event dict. Raises descriptive exceptions on failure.
    """
    required_fields = {"id", "type", "artifact_sha", "repo", "status"}
    missing = required_fields - set(event.keys())
    if missing:
        raise SchemaValidationError(f"Missing required fields: {missing}")

    if event.get("artifact_sha") is None:
        raise SchemaValidationError("Field 'artifact_sha' must not be null")

    if event["type"] not in KNOWN_EVENT_TYPES:
        raise UnknownEventTypeError(
            f"Unknown event type '{event['type']}'. "
            f"Expected one of: {KNOWN_EVENT_TYPES}"
        )

def process_event(event: dict) -> None:
    """
    Simulate downstream processing of a valid event.
    In a real pipeline this might write to a database, call an API, etc.
    """
    validate_event(event)
    print(f"    ✓ Processed: id={event['id']} type={event['type']}")


# ---------------------------------------------------------------------------
# DLQ routing
# ---------------------------------------------------------------------------

def send_to_dlq(
    producer: KafkaProducer,
    original_record,
    error: Exception,
    retry_count: int,
) -> None:
    """
    Route a failed message to the DLQ topic, enriching it with error metadata
    as Kafka headers.
    """
    headers = [
        ("dlq.original.topic",     SOURCE_TOPIC.encode()),
        ("dlq.original.partition", str(original_record.partition).encode()),
        ("dlq.original.offset",    str(original_record.offset).encode()),
        ("dlq.error.type",         type(error).__name__.encode()),
        ("dlq.error.message",      str(error).encode()),
        ("dlq.retry.count",        str(retry_count).encode()),
        ("dlq.timestamp",          datetime.datetime.utcnow().isoformat().encode()),
        ("dlq.consumer.group",     CONSUMER_GROUP.encode()),
    ]

    future = producer.send(
        DLQ_TOPIC,
        key=original_record.key,
        value=original_record.value,   # preserve original bytes unchanged
        headers=headers,
    )
    meta = future.get(timeout=5)
    print(
        f"    ✗ → DLQ  {meta.topic}:{meta.partition}@{meta.offset}  "
        f"error={type(error).__name__}: {str(error)[:80]}"
    )


# ---------------------------------------------------------------------------
# Main consumer loop
# ---------------------------------------------------------------------------

def main():
    consumer = KafkaConsumer(
        SOURCE_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,       # manual commit: only after success or DLQ
        value_deserializer=lambda b: b, # keep raw bytes; we deserialize manually
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k if isinstance(k, bytes) else k.encode() if k else None,
    )

    print(f"Consuming from: {SOURCE_TOPIC}  →  DLQ: {DLQ_TOPIC}")
    print(f"Consumer group: {CONSUMER_GROUP}  |  Max retries: {MAX_RETRIES}\n")

    try:
        for record in consumer:
            print(f"  MSG  partition={record.partition} offset={record.offset}")
            raw = record.value

            retry_count = 0
            last_error = None
            processed = False

            while retry_count <= MAX_RETRIES:
                try:
                    # Step 1: deserialize
                    try:
                        event = json.loads(raw.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        raise SchemaValidationError(f"Deserialization failed: {e}") from e

                    # Step 2: validate + process
                    process_event(event)
                    processed = True
                    break

                except (SchemaValidationError, UnknownEventTypeError) as e:
                    # These are non-retryable — go straight to DLQ
                    last_error = e
                    print(f"    Non-retryable error (attempt {retry_count+1}): {e}")
                    break

                except Exception as e:
                    # These might be transient (network, downstream service down)
                    last_error = e
                    retry_count += 1
                    if retry_count <= MAX_RETRIES:
                        backoff = 0.5 * (2 ** (retry_count - 1))
                        print(f"    Transient error (attempt {retry_count}/{MAX_RETRIES}), "
                              f"retrying in {backoff:.1f}s: {e}")
                        time.sleep(backoff)
                    else:
                        print(f"    Retry budget exhausted after {MAX_RETRIES} attempts.")
                        break

            if not processed and last_error is not None:
                send_to_dlq(producer, record, last_error, retry_count)

            # Commit offset regardless of outcome — message is either processed
            # or safely stored in the DLQ. Never leave the offset uncommitted.
            consumer.commit()

    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        consumer.close()
        producer.close()


if __name__ == "__main__":
    main()
```

### 3.2 Run the consumer

In a second terminal:

```bash
python consumer_with_dlq.py
```

Then in your first terminal, run the producer again if needed:

```bash
python producer.py
```

Watch the consumer output. You should see valid events processed with `✓` and
broken events routed to the DLQ with `✗ → DLQ`.

**Expected output:**

```text
Consuming from: epr.events  →  DLQ: epr.events.dlq
Consumer group: epr-validator-v1  |  Max retries: 3

  MSG  partition=0 offset=0
    ✓ Processed: id=... type=build.finished
  MSG  partition=1 offset=0
    ✓ Processed: id=... type=test.passed
  MSG  partition=2 offset=0
    Non-retryable error (attempt 1): Missing required fields: {'artifact_sha'}
    ✗ → DLQ  epr.events.dlq:2@0  error=SchemaValidationError: Missing required fields: ...
  ...
```

---

## Part 4 — Inspecting the DLQ

### 4.1 View raw DLQ messages with `rpk`

```bash
docker exec -it redpanda \
    rpk topic consume epr.events.dlq \
    --brokers localhost:9092 \
    --offset start \
    --format json \
    --num 10
```

You will see the original message bytes alongside Kafka metadata. The error
details are in the headers.

### 4.2 Decode headers with `rpk`

`rpk` displays headers as base64 by default. To view them in a readable format:

```bash
docker exec -it redpanda \
    rpk topic consume epr.events.dlq \
    --brokers localhost:9092 \
    --offset start \
    --format '%v\n%h\n---\n' \
    --num 10
```

### 4.3 Check DLQ topic stats

```bash
# Message count per partition
docker exec -it redpanda \
    rpk topic describe epr.events.dlq --brokers localhost:9092

# Consumer lag for a hypothetical DLQ processor
docker exec -it redpanda \
    rpk group describe epr-dlq-processor --brokers localhost:9092
```

### 4.4 Write a DLQ inspector script

Create `dlq_inspector.py` to pretty-print DLQ contents:

```python
#!/usr/bin/env python3
"""
Lab 05 DLQ inspector — reads the DLQ and pretty-prints error metadata.
"""

import json
from kafka import KafkaConsumer

BOOTSTRAP = "localhost:9092"
DLQ_TOPIC = "epr.events.dlq"

def decode_headers(headers):
    return {k: v.decode("utf-8", errors="replace") for k, v in headers}

def main():
    consumer = KafkaConsumer(
        DLQ_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="epr-dlq-inspector",
        auto_offset_reset="earliest",
        consumer_timeout_ms=3000,
    )

    print(f"{'='*70}")
    print(f"DLQ Inspector — {DLQ_TOPIC}")
    print(f"{'='*70}\n")

    count = 0
    for record in consumer:
        count += 1
        headers = decode_headers(record.headers)

        print(f"Message #{count}")
        print(f"  Kafka:     partition={record.partition} offset={record.offset}")
        print(f"  Origin:    topic={headers.get('dlq.original.topic')} "
              f"partition={headers.get('dlq.original.partition')} "
              f"offset={headers.get('dlq.original.offset')}")
        print(f"  Error:     [{headers.get('dlq.error.type')}] "
              f"{headers.get('dlq.error.message')}")
        print(f"  Retries:   {headers.get('dlq.retry.count')}")
        print(f"  DLQ'd at:  {headers.get('dlq.timestamp')}")
        print(f"  Consumer:  {headers.get('dlq.consumer.group')}")

        # Try to pretty-print the original payload
        try:
            payload = json.loads(record.value.decode("utf-8"))
            print(f"  Payload:   {json.dumps(payload, indent=4)}")
        except Exception:
            print(f"  Payload:   (non-JSON) {record.value[:100]}")

        print()

    consumer.close()
    print(f"Total DLQ messages: {count}")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python dlq_inspector.py
```

---

## Part 5 — Replaying Fixed Messages

A DLQ is only useful if you can act on its contents. In this section you will
fix broken messages and replay them into the source topic.

### 5.1 Create `dlq_reprocessor.py`

```python
#!/usr/bin/env python3
"""
Lab 05 DLQ reprocessor — fixes broken messages and replays them to the
source topic. Extend the fix_message() function for your own rules.
"""

import json
import uuid
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP = "localhost:9092"
DLQ_TOPIC = "epr.events.dlq"
SOURCE_TOPIC = "epr.events"
REPLAY_GROUP = "epr-dlq-reprocessor"

KNOWN_EVENT_TYPES = {"build.finished", "test.passed", "deploy.started", "deploy.finished"}


def fix_message(payload: dict, error_type: str, error_msg: str):
    """
    Attempt to fix a broken message based on the recorded error.
    Returns (fixed_payload, was_fixed) tuple.
    Extend this function with your domain-specific repair logic.
    """

    if "Missing required fields" in error_msg and "artifact_sha" in error_msg:
        # Back-fill with a sentinel so the record is marked as repaired
        payload["artifact_sha"] = "UNKNOWN-REPAIRED"
        payload["_dlq_repaired"] = True
        return payload, True

    if "artifact_sha' must not be null" in error_msg:
        payload["artifact_sha"] = "UNKNOWN-REPAIRED"
        payload["_dlq_repaired"] = True
        return payload, True

    if "Unknown event type" in error_msg:
        # Map to a catch-all type rather than discard
        payload["type"] = "unknown.event"
        payload["_original_type"] = payload.get("type", "")
        payload["_dlq_repaired"] = True
        return payload, True

    # Cannot fix — will be skipped (or could be re-DLQ'd to a quarantine topic)
    return payload, False


def decode_headers(headers):
    return {k: v.decode("utf-8", errors="replace") for k, v in headers}


def main():
    consumer = KafkaConsumer(
        DLQ_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=REPLAY_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=3000,
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    replayed = skipped = 0

    for record in consumer:
        headers = decode_headers(record.headers)
        error_type = headers.get("dlq.error.type", "")
        error_msg  = headers.get("dlq.error.message", "")

        try:
            payload = json.loads(record.value.decode("utf-8"))
        except Exception as e:
            print(f"  SKIP  Cannot deserialize DLQ message: {e}")
            skipped += 1
            consumer.commit()
            continue

        fixed_payload, was_fixed = fix_message(payload, error_type, error_msg)

        if was_fixed:
            future = producer.send(SOURCE_TOPIC, value=fixed_payload)
            meta = future.get(timeout=5)
            print(
                f"  REPLAY  → {meta.topic}:{meta.partition}@{meta.offset}  "
                f"id={fixed_payload.get('id', '?')}"
            )
            replayed += 1
        else:
            print(f"  SKIP  No fix rule for [{error_type}]: {error_msg[:60]}")
            skipped += 1

        consumer.commit()

    consumer.close()
    producer.flush()
    producer.close()

    print(f"\nReplayed: {replayed}  |  Skipped: {skipped}")


if __name__ == "__main__":
    main()
```

### 5.2 Run the reprocessor

```bash
python dlq_reprocessor.py
```

Then restart the main consumer (reset its offset or use a new group) to verify
the replayed messages are now processed successfully:

```bash
# Consume from start with a fresh group to verify replayed messages
docker exec -it redpanda \
    rpk topic consume epr.events \
    --brokers localhost:9092 \
    --offset start \
    --format json \
    --num 20
```

Look for messages with `"_dlq_repaired": true` — these are your fixed events
flowing through the pipeline cleanly.

---

## Part 6 — Challenge Exercises

Work through these on your own. Solutions are not provided — use what you've
built as a starting point.

### Challenge A: Retry topic (tiered DLQ)

Implement a two-tier error handling chain:

```text
epr.events  →  epr.events.retry  →  epr.events.dlq
```

Messages that fail with a _transient_ error go to `epr.events.retry` first. A
retry consumer re-attempts them with exponential back-off. Only after
`MAX_RETRY_ATTEMPTS` from the retry topic do they graduate to the DLQ.

Hint: use the `dlq.retry.count` header to track cumulative attempts across both
tiers.

### Challenge B: DLQ monitoring with rpk and alerting

Write a shell script `dlq_monitor.sh` that:

1. Queries the `epr.events.dlq` high watermark every 30 seconds using
   `rpk topic describe`
2. Compares it to the previous reading to calculate messages-per-minute
3. Prints a `⚠ ALERT` line when the rate exceeds a threshold (e.g., 5
   messages/minute)

### Challenge C: Schema Registry integration

Modify the consumer to use Redpanda's Schema Registry (available at
`http://localhost:8081` in the default Docker Compose setup):

1. Register a JSON Schema for EPR events
2. Replace the manual `validate_event()` function with schema registry
   validation
3. Ensure schema violations land in the DLQ with
   `dlq.error.type=SchemaRegistryValidationError`

Useful endpoint:

```bash
curl -s http://localhost:8081/subjects
curl -s http://localhost:8081/subjects/epr.events-value/versions/latest
```

### Challenge D: DLQ quarantine for poison pills

Some messages cannot be fixed and should never re-enter the main pipeline. Add a
**quarantine topic** (`epr.events.quarantine`) to `dlq_reprocessor.py`. Messages
that the reprocessor cannot fix after a configurable number of attempts are
moved to quarantine rather than remaining in the DLQ indefinitely.

---

## Cleanup

```bash
# Remove lab topics
docker exec -it redpanda \
    rpk topic delete epr.events epr.events.dlq

# If you created the retry/quarantine topics in the challenges
docker exec -it redpanda \
    rpk topic delete epr.events.retry epr.events.quarantine
```

---

**Duration:** ~60 minutes **Prerequisites:** Labs 01–04 complete; Redpanda
running locally via Docker Compose; `rpk` CLI available; Python 3.12+ with
`kafka-python-ng` installed.

---

## Key Takeaways

- **DLQs prevent pipeline stalls** without silently dropping data. They are the
  difference between a resilient system and a fragile one.
- **Always enrich DLQ messages with headers.** The original payload alone is not
  enough — you need the error context, retry count, timestamp, and consumer
  group to diagnose and fix problems efficiently.
- **Commit offsets only after a message is either processed or DLQ'd.**
  Committing before routing to the DLQ risks losing the error record if the DLQ
  write fails.
- **Distinguish retryable from non-retryable errors.** Schema validation
  failures will never succeed on retry; network timeouts might. Model this
  explicitly in your error handler.
- **DLQ retention should be longer than the source topic's retention.**
  Operators need time to investigate — treat the DLQ as a forensic store.
- **Build the reprocessor before you need it.** A DLQ with no reprocessing path
  is just a slightly-nicer way to lose messages.

---

## Further Reading

- [Redpanda Documentation — Topics](https://docs.redpanda.com/current/develop/produce-data/configure-producers/)
- [Redpanda `rpk` CLI Reference](https://docs.redpanda.com/current/reference/rpk/)
- [Confluent: What is a Kafka Dead Letter Queue?](https://www.confluent.io/learn/kafka-dead-letter-queue/)
- [kafka-python Documentation](https://kafka-python.readthedocs.io/)
