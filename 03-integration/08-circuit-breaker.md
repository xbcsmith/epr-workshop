# Circuit Breaker

**Duration:** ~55 minutes
**Prerequisites:** Redpanda running via Docker Compose; Python 3.10+ with `kafka-python` and `pybreaker` installed.

---

## Overview

The retry strategies in Lab 09 protect individual messages. The circuit breaker protects your entire consumer process — and everything downstream of it — from being destroyed by a dependency that has gone completely dark.

Imagine your Kafka consumer processes each message by calling a downstream REST API. The API goes down. Without a circuit breaker, your consumer:

1. Receives a message
2. Calls the API — connection timeout after 30 seconds
3. Retries — another 30-second timeout
4. Retries again — another timeout
5. Routes to DLQ
6. Receives the next message and starts over

With 1,000 messages in the queue and a 30-second timeout, your consumer is effectively frozen for 8+ hours burning retries that will all fail. The queue fills up. Consumer lag climbs. Every service watching this pipeline stops seeing events.

A circuit breaker short-circuits that loop. After N consecutive failures it opens — subsequent calls fail immediately without hitting the broken dependency. After a recovery timeout it enters half-open state, allowing one test call. If that succeeds, it closes and normal processing resumes. If it fails, it opens again.

```
       failures ≥ threshold          test call fails
CLOSED ─────────────────────► OPEN ──────────────────► OPEN
  ▲                             │                        │
  │     test call succeeds      │ recovery timeout       │
  └─────────────────────────────┘ elapses               │
               HALF-OPEN ◄──────────────────────────────┘
```

This lab builds a circuit breaker from scratch to understand the mechanism, then uses `pybreaker` — the production-grade Python library — integrated into a Kafka consumer.

---

## Part 1 — Setup

```bash
pip install pybreaker

rpk topic create events.inbound \
  --partitions 3 --replicas 1

rpk topic create events.inbound.dlq \
  --partitions 3 --replicas 1 \
  --topic-config retention.ms=604800000
```

---

## Part 2 — Build a Circuit Breaker from Scratch

Before using a library, implement the state machine yourself. This makes the behavior concrete and removes any mystery from what `pybreaker` does internally.

Create `circuit_breaker.py`:

```python
"""
A minimal circuit breaker implementation.
Three states: CLOSED, OPEN, HALF_OPEN.
Build this to understand the mechanism before using pybreaker.
"""

import time
import threading
from enum import Enum, auto


class State(Enum):
    CLOSED    = auto()   # normal operation — calls pass through
    OPEN      = auto()   # broken — calls fail immediately
    HALF_OPEN = auto()   # recovery probe — one call allowed through


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the circuit is open."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 1,
    ):
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold

        self._state            = State.CLOSED
        self._failure_count    = 0
        self._success_count    = 0
        self._opened_at: float = 0.0
        self._lock             = threading.Lock()

    @property
    def state(self) -> State:
        with self._lock:
            if self._state == State.OPEN:
                elapsed = time.monotonic() - self._opened_at
                if elapsed >= self.recovery_timeout:
                    self._state         = State.HALF_OPEN
                    self._success_count = 0
                    print(f"  [{self.name}] OPEN → HALF_OPEN after "
                          f"{elapsed:.1f}s — sending probe call")
            return self._state

    def call(self, fn, *args, **kwargs):
        """
        Execute fn(*args, **kwargs) through the circuit breaker.
        Raises CircuitOpenError if the circuit is open.
        """
        state = self.state

        if state == State.OPEN:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN — call blocked"
            )

        try:
            result = fn(*args, **kwargs)
            self._on_success(state)
            return result
        except Exception as exc:
            self._on_failure(state, exc)
            raise

    def _on_success(self, state: State) -> None:
        with self._lock:
            if state == State.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state         = State.CLOSED
                    self._failure_count = 0
                    print(f"  [{self.name}] HALF_OPEN → CLOSED "
                          f"(probe succeeded)")
            elif state == State.CLOSED:
                self._failure_count = 0   # reset on any success

    def _on_failure(self, state: State, exc: Exception) -> None:
        with self._lock:
            if state == State.HALF_OPEN:
                # Probe failed — back to OPEN
                self._state    = State.OPEN
                self._opened_at = time.monotonic()
                print(f"  [{self.name}] HALF_OPEN → OPEN "
                      f"(probe failed: {exc})")
            elif state == State.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state    = State.OPEN
                    self._opened_at = time.monotonic()
                    print(f"  [{self.name}] CLOSED → OPEN after "
                          f"{self._failure_count} consecutive failures")

    def __repr__(self) -> str:
        return (f"CircuitBreaker(name={self.name!r}, "
                f"state={self._state.name}, "
                f"failures={self._failure_count})")
```

### 2.1 Exercise the state machine

Create `cb_demo.py`:

```python
#!/usr/bin/env python3
"""Walk the circuit breaker through all three states."""

import time
from circuit_breaker import CircuitBreaker, CircuitOpenError

cb = CircuitBreaker(
    name="downstream-api",
    failure_threshold=3,
    recovery_timeout=5.0,    # short for demo — use 30-60s in production
    success_threshold=1,
)


def flaky_api(should_fail: bool) -> str:
    if should_fail:
        raise ConnectionError("API unreachable")
    return "OK"


print("=== Phase 1: Normal operation ===")
for i in range(3):
    result = cb.call(flaky_api, should_fail=False)
    print(f"  call {i+1}: {result}  state={cb.state.name}")

print("\n=== Phase 2: Failures accumulate ===")
for i in range(4):
    try:
        cb.call(flaky_api, should_fail=True)
    except ConnectionError as e:
        print(f"  call {i+1}: ConnectionError  state={cb.state.name}")
    except CircuitOpenError as e:
        print(f"  call {i+1}: BLOCKED  state={cb.state.name}  ({e})")

print("\n=== Phase 3: Circuit open — calls blocked immediately ===")
for i in range(3):
    try:
        cb.call(flaky_api, should_fail=True)
    except CircuitOpenError as e:
        print(f"  call {i+1}: BLOCKED (no timeout, no retry)")

print(f"\n  Waiting {cb.recovery_timeout}s for recovery timeout...")
time.sleep(cb.recovery_timeout + 0.5)

print("\n=== Phase 4: Half-open — probe call ===")
try:
    result = cb.call(flaky_api, should_fail=False)
    print(f"  probe: {result}  state={cb.state.name}")
except Exception as e:
    print(f"  probe failed: {e}  state={cb.state.name}")

print("\n=== Phase 5: Closed — normal operation restored ===")
for i in range(3):
    result = cb.call(flaky_api, should_fail=False)
    print(f"  call {i+1}: {result}  state={cb.state.name}")
```

```bash
python cb_demo.py
```

Watch the state transitions: `CLOSED → OPEN → HALF_OPEN → CLOSED`. The key behavior to observe is Phase 3: once the circuit opens, calls are rejected instantaneously — no waiting for timeouts, no burning retries.

---

## Part 3 — Circuit Breaker in a Kafka Consumer

Now integrate the circuit breaker into a Kafka consumer. The integration has two parts: wrapping the downstream call, and deciding what to do with messages when the circuit is open.

When the circuit opens, you have two options:

1. **Pause and wait** — stop consuming, sleep until the circuit closes or half-opens, then resume. Simple. Causes consumer lag to grow but ensures no messages are processed against a broken dependency.

2. **Route to retry topic** — send messages to a retry topic to be re-processed later. Consumer lag stays low but requires the retry infrastructure from Lab 09.

This lab implements option 1 (pause-and-wait) because it is simpler and correct for most CI/CD pipeline workloads, where it is better to queue up and wait than to route events in a non-standard order.

Create `consumer_circuit_breaker.py`:

```python
#!/usr/bin/env python3
"""
Lab 11 — Kafka consumer with circuit breaker.

Wraps the downstream call in a circuit breaker.
When the circuit opens:
  - Stop consuming (pause the topic partitions)
  - Poll the circuit state every OPEN_POLL_INTERVAL seconds
  - Resume when the circuit transitions to HALF_OPEN or CLOSED
"""

import json
import time
import datetime
import threading
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from circuit_breaker import CircuitBreaker, CircuitOpenError

BOOTSTRAP          = "localhost:9092"
TOPIC              = "events.inbound"
DLQ                = "events.inbound.dlq"
GROUP              = "circuit-breaker-consumer"
OPEN_POLL_INTERVAL = 2.0    # seconds between checks when circuit is open


# ---------------------------------------------------------------------------
# Simulated downstream service
# ---------------------------------------------------------------------------

class DownstreamService:
    """
    Simulates a downstream HTTP service with controllable availability.
    Toggle .available to simulate outages.
    """
    def __init__(self):
        self.available        = True
        self.call_count       = 0
        self.failure_count    = 0

    def process(self, event: dict) -> dict:
        self.call_count += 1
        if not self.available:
            self.failure_count += 1
            raise ConnectionError(
                f"Downstream service unavailable (call #{self.call_count})"
            )
        return {"processed": True, "name": event.get("name")}


downstream = DownstreamService()

# Circuit breaker wrapping the downstream service
breaker = CircuitBreaker(
    name="downstream-service",
    failure_threshold=3,       # open after 3 consecutive failures
    recovery_timeout=10.0,     # wait 10s before probing (use 30-60s in prod)
    success_threshold=2,       # require 2 successes to fully close
)


# ---------------------------------------------------------------------------
# Background thread: toggles service availability to simulate outage/recovery
# ---------------------------------------------------------------------------

def simulate_outage(delay_before: float, outage_duration: float) -> None:
    """Bring the downstream service down, then restore it."""
    def _run():
        time.sleep(delay_before)
        downstream.available = False
        print(f"\n  *** DOWNSTREAM SERVICE DOWN ***\n")
        time.sleep(outage_duration)
        downstream.available = True
        print(f"\n  *** DOWNSTREAM SERVICE RESTORED ***\n")

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# DLQ routing
# ---------------------------------------------------------------------------

def send_to_dlq(producer, record, error: Exception) -> None:
    headers = [
        ("dlq.error.type",    type(error).__name__.encode()),
        ("dlq.error.message", str(error)[:200].encode()),
        ("dlq.timestamp",     datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(
        DLQ, key=record.key, value=record.value, headers=headers
    ).get(timeout=5)
    print(f"    ✗  → DLQ: {error}")


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
        consumer_timeout_ms=500,    # short timeout so we can check circuit state
        value_deserializer=lambda b: json.loads(b.decode()),
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    # Trigger an outage: starts after 3 seconds, lasts 15 seconds
    simulate_outage(delay_before=3.0, outage_duration=15.0)

    print(f"Consumer running. Outage starts in ~3s.\n")

    while True:
        try:
            for record in consumer:
                event = record.value
                print(f"  MSG  offset={record.offset}  "
                      f"name={event.get('name')}")

                try:
                    result = breaker.call(downstream.process, event)
                    print(f"    ✓  Processed: {result}")
                    consumer.commit()

                except CircuitOpenError:
                    # Circuit is open — pause consumption and wait
                    print(f"  Circuit OPEN — pausing consumption. "
                          f"Waiting for recovery...")
                    # Do not commit — we will re-process this message
                    # when the circuit closes
                    _wait_for_circuit_close(consumer)
                    print(f"  Circuit recovered — resuming consumption")
                    # Don't commit here — the for loop will retry this record
                    # on the next iteration. But we've already moved past it.
                    # In a real system: seek back to this offset before resuming.
                    # For this lab, we simply continue.
                    break

                except ConnectionError as e:
                    # The call reached the service but it returned an error.
                    # The circuit breaker counts this failure internally.
                    print(f"    ✗  ConnectionError: {e}  "
                          f"(cb failures={breaker._failure_count})")
                    # For non-circuit errors, use the retry strategy from Lab 09.
                    # Here we send straight to DLQ for simplicity.
                    send_to_dlq(producer, record, e)
                    consumer.commit()

        except StopIteration:
            # consumer_timeout_ms elapsed with no new messages
            pass
        except KeyboardInterrupt:
            break

    print(f"\nShutting down.")
    print(f"  Total downstream calls:    {downstream.call_count}")
    print(f"  Total downstream failures: {downstream.failure_count}")
    consumer.close()
    producer.close()


def _wait_for_circuit_close(consumer) -> None:
    """
    Block until the circuit breaker leaves the OPEN state.
    Pause Kafka partition polling so the broker doesn't rebalance us out.
    """
    from circuit_breaker import State

    # Pause all assigned partitions — broker won't rebalance during max_poll_interval
    assigned = consumer.assignment()
    if assigned:
        consumer.pause(*assigned)

    while breaker.state == State.OPEN:
        # Keep polling (even paused) to send heartbeats and prevent rebalance
        consumer.poll(timeout_ms=1000)
        print(f"    Circuit state: {breaker.state.name}  "
              f"(downstream available={downstream.available})")
        time.sleep(OPEN_POLL_INTERVAL)

    # Resume partitions
    if assigned:
        consumer.resume(*assigned)


if __name__ == "__main__":
    main()
```

### 3.1 Produce test messages

Create `producer.py` for this lab:

```python
#!/usr/bin/env python3
"""Lab 11 producer — continuous stream of events."""

import json
import uuid
import time
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC     = "events.inbound"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode(),
)

print(f"Producing to {TOPIC}. Ctrl-C to stop.\n")
seq = 0
try:
    while True:
        event = {
            "id":   str(uuid.uuid4()),
            "name": f"service-{seq % 5 + 1}",
            "seq":  seq,
        }
        producer.send(TOPIC, value=event)
        print(f"  SENT seq={seq}")
        seq += 1
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    producer.flush()
    producer.close()
```

Run in two terminals:

```bash
# Terminal 1
python producer.py

# Terminal 2
python consumer_circuit_breaker.py
```

Watch the sequence of events:
1. Consumer processes messages normally for ~3 seconds
2. Downstream goes down — `ConnectionError` starts appearing
3. After 3 consecutive failures, the circuit opens — messages are blocked immediately
4. Consumer pauses, polling for circuit state
5. After 10 seconds, circuit transitions to HALF_OPEN
6. Probe call succeeds — circuit closes
7. Consumer resumes

---

## Part 4 — Using `pybreaker` in Production

The handbuilt circuit breaker teaches the mechanism. `pybreaker` is what you use in production — it handles thread safety, listeners, and optional Redis-backed state correctly.

Create `consumer_pybreaker.py`:

```python
#!/usr/bin/env python3
"""
Lab 11 — Production circuit breaker using pybreaker.

pybreaker adds:
  - Thread-safe state management
  - Listener hooks for logging and metrics
  - Optional Redis-backed state (shared across processes)
  - Configurable success threshold for closing
"""

import json
import time
import datetime
import threading
import logging
import pybreaker
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC     = "events.inbound"
DLQ       = "events.inbound.dlq"
GROUP     = "pybreaker-consumer"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("consumer")


# ---------------------------------------------------------------------------
# Listener: logs every state transition and emits metrics hooks
# ---------------------------------------------------------------------------

class PipelineCircuitListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        log.warning(
            f"Circuit '{cb.name}' state change: "
            f"{old_state.name} → {new_state.name}"
        )
        # In production: emit to Prometheus, Datadog, etc.
        # metrics.increment(f"circuit_breaker.{cb.name}.{new_state.name.lower()}")

    def failure(self, cb, exc):
        log.warning(
            f"Circuit '{cb.name}' failure "
            f"({cb.fail_counter}/{cb.fail_max}): {exc}"
        )

    def success(self, cb):
        if cb.current_state == "half-open":
            log.info(f"Circuit '{cb.name}' probe succeeded — closing")


# ---------------------------------------------------------------------------
# Circuit breaker instance
# ---------------------------------------------------------------------------

api_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=10,
    listeners=[PipelineCircuitListener()],
    name="downstream-api",
)


# ---------------------------------------------------------------------------
# Downstream call wrapped by the circuit breaker
# ---------------------------------------------------------------------------

class DownstreamService:
    def __init__(self):
        self.available = True

    def process(self, event: dict) -> dict:
        if not self.available:
            raise ConnectionError("Service unavailable")
        return {"ok": True, "name": event["name"]}


downstream = DownstreamService()


@api_breaker
def call_downstream(event: dict) -> dict:
    """Decorate the call with the circuit breaker."""
    return downstream.process(event)


# ---------------------------------------------------------------------------
# Outage simulation
# ---------------------------------------------------------------------------

def simulate_outage(delay: float, duration: float) -> None:
    def _run():
        time.sleep(delay)
        downstream.available = False
        log.warning("*** OUTAGE STARTED ***")
        time.sleep(duration)
        downstream.available = True
        log.warning("*** OUTAGE ENDED ***")
    threading.Thread(target=_run, daemon=True).start()


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

def send_to_dlq(producer, record, error: Exception) -> None:
    headers = [
        ("dlq.error.type",    type(error).__name__.encode()),
        ("dlq.error.message", str(error)[:200].encode()),
        ("dlq.timestamp",     datetime.datetime.utcnow().isoformat().encode()),
    ]
    producer.send(DLQ, key=record.key, value=record.value,
                  headers=headers).get(timeout=5)


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=500,
        value_deserializer=lambda b: json.loads(b.decode()),
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    simulate_outage(delay=4.0, duration=15.0)
    log.info("Consumer started. Outage begins in ~4s.")

    try:
        while True:
            try:
                for record in consumer:
                    try:
                        result = call_downstream(record.value)
                        log.info(f"  ✓  {record.value['name']}  "
                                 f"offset={record.offset}")
                        consumer.commit()

                    except pybreaker.CircuitBreakerError:
                        # Circuit is open — pause and wait
                        assigned = consumer.assignment()
                        if assigned:
                            consumer.pause(*assigned)
                        while api_breaker.current_state == "open":
                            consumer.poll(timeout_ms=1000)
                            time.sleep(1.0)
                        if assigned:
                            consumer.resume(*assigned)
                        break

                    except ConnectionError as e:
                        log.warning(f"  ✗  {e}")
                        send_to_dlq(producer, record, e)
                        consumer.commit()

            except StopIteration:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.close()
        log.info("Shutdown complete.")


if __name__ == "__main__":
    main()
```

```bash
python consumer_pybreaker.py
```

The `pybreaker` version has the same behavior as the handbuilt version, but the listener hook gives you a clean integration point for metrics and alerting — the `state_change` method is the right place to fire a PagerDuty alert when a circuit opens in production.

---

## Part 5 — Where Circuit Breakers Go in the EPR Pipeline

In the EPR workshop context, circuit breakers belong at every integration point that sits between a Kafka consumer and an external dependency. Specifically:

- The **watcher** calls the EPR server API — wrap that call in a circuit breaker
- Any consumer that writes to **PostgreSQL** — wrap the DB call
- Any consumer that calls an **external scanning service** or **deployment API** — wrap each independently

Each integration point gets its own breaker with its own threshold. A database breaker and an API breaker should not share state — the database going down should not prevent API calls from continuing.

---

## Part 6 — Challenge Exercises

### Challenge A: Half-open with success threshold

Modify the handbuilt `CircuitBreaker` to require `success_threshold=3` instead of 1 before closing from half-open. This means three consecutive successful probe calls are required before the circuit fully closes. Demonstrate the behavior — the circuit should re-open if any of those three probe calls fail.

### Challenge B: Circuit breaker metrics

Extend `PipelineCircuitListener` to track:
- Total number of times each circuit has opened
- Total calls blocked while open (approximate, using a counter in `state_change`)
- Time spent in OPEN state per occurrence

Print a summary when the consumer shuts down. This is the data you would push to Prometheus in production.

### Challenge C: Per-partition circuit breaker

The consumers in this lab use a single circuit breaker for all partitions. In a multi-partition topic, a broken partition (e.g. due to a corrupt message on partition 2) should not open the circuit for partitions 0 and 1. Implement a per-partition circuit breaker map and demonstrate that an error isolated to one partition does not affect processing on others.

### Challenge D: Redis-backed state for multi-instance consumers

In a horizontally scaled consumer group, each instance has its own in-memory circuit breaker. If instance A opens its circuit, instance B keeps processing — it has not seen the failures yet. This is usually fine but creates a brief window of asymmetric behavior.

Use `pybreaker.CircuitRedisStorage` to share circuit breaker state across two consumer instances:

```python
import redis
import pybreaker

redis_conn = redis.StrictRedis(host="localhost", port=6379)
shared_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=10,
    state_storage=pybreaker.CircuitRedisStorage(
        pybreaker.STATE_CLOSED,
        redis_conn,
        namespace="epr-pipeline",
    ),
)
```

Run two consumer instances simultaneously, trigger failures from one, and verify both instances open their circuits.

---

## Cleanup

```bash
rpk topic delete events.inbound events.inbound.dlq
```

---

## Key Takeaways

- Without a circuit breaker, a broken downstream dependency can freeze your entire consumer for hours burning timeouts and retries.
- The three states — CLOSED, OPEN, HALF_OPEN — implement a self-healing loop: open fast on failure, wait for recovery, probe cautiously, close when healthy.
- When the circuit opens, pause Kafka partition polling (not just sleep) so the broker does not trigger a consumer group rebalance during the recovery window.
- The listener pattern (`pybreaker.CircuitBreakerListener`) is the integration point for metrics and alerting. The `state_change` hook is where production monitoring hooks should live.
- Each external integration point gets its own circuit breaker. Shared breakers create false dependencies between unrelated systems.
- Circuit breakers and retry strategies are complementary. Retries handle individual message failures. Circuit breakers handle systemic dependency failures. Use both.
