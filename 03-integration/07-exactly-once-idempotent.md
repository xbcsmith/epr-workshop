# Exactly-Once Semantics and Idempotent Producers

## Overview

Every Kafka/Redpanda producer has a delivery guarantee. Understanding which
guarantee you have — and what it costs to upgrade it — is one of the most
important configuration decisions in an event-driven pipeline.

There are three levels:

| Guarantee     | What it means                              | Config                                 |
| ------------- | ------------------------------------------ | -------------------------------------- |
| At-most-once  | Messages may be lost, never duplicated     | `acks=0` or `acks=1`, no retries       |
| At-least-once | Messages are never lost, may be duplicated | `acks=all`, retries > 0                |
| Exactly-once  | Messages are never lost, never duplicated  | `enable_idempotence=True` + `acks=all` |

---

Most pipelines that think they have at-least-once actually have at-most-once
because they haven't set `acks=all`. Most pipelines that think they have
exactly-once actually have at-least-once because they haven't enabled
idempotence.

This lab demonstrates each guarantee experimentally — you will see duplicates
appear without idempotence and disappear with it — then covers the transactional
producer for the cases where idempotence alone isn't sufficient.

---

## Background: How Duplicates Happen

Consider a producer that sends a message, waits for an acknowledgement, and the
network drops the response:

```text
Producer                    Redpanda broker
   │                              │
   │──── ProduceRequest ─────────►│
   │                              │ (writes to log)
   │◄─── ProduceResponse ─────────│
   │         (LOST)               │
   │                              │
   │  (timeout — did it arrive?)  │
   │──── ProduceRequest (RETRY) ──►│
   │                              │ (writes AGAIN — duplicate!)
   │◄─── ProduceResponse ─────────│
```

---

The broker wrote the message successfully both times. The producer had no way to
know the first write succeeded because the response was lost. Without
idempotence, this retry produces a duplicate that is indistinguishable from the
original.

Idempotent producers solve this by assigning every message a producer ID (PID)
and a monotonically increasing sequence number. The broker tracks the last
sequence number it accepted from each PID. If it sees a sequence number it has
already processed, it discards the duplicate and sends back a success response —
from the producer's perspective the send succeeded, but no duplicate was
written.

---

## Part 1 — Setup

```bash
docker exec -it redpanda \
    rpk topic create delivery.demo \
    --partitions 1 \
    --replicas 1

docker exec -it redpanda \
    rpk topic create delivery.transactions \
    --partitions 1 \
    --replicas 1 \
    --topic-config min.insync.replicas=1
```

A single partition is intentional for this lab — it makes sequence numbers
easier to reason about.

---

## Part 2 — Demonstrate At-Least-Once Duplicates

First, reproduce the duplicate problem. This producer simulates a network drop
by catching the response, then retrying as if it never arrived.

Create `producer_at_least_once.py`:

```python
#!/usr/bin/env python3
"""
Lab 10 — At-least-once producer.

Simulates the network-drop scenario: a successful send whose response
is "lost", causing the producer to retry and produce a duplicate.
"""

import json
import uuid
from kafka import KafkaProducer
from kafka.errors import KafkaError

BOOTSTRAP = "localhost:9092"
TOPIC     = "delivery.demo"


def make_event(name: str, seq: int) -> dict:
    return {"id": str(uuid.uuid4()), "name": name, "seq": seq}


def main():
    # At-least-once config: acks=all + retries, but no idempotence
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        acks="all",
        retries=3,
        value_serializer=lambda v: json.dumps(v).encode(),
    )

    events = [make_event("service-a", i) for i in range(5)]

    for event in events:
        # Normal send
        producer.send(TOPIC, value=event).get(timeout=5)
        print(f"  SENT:   seq={event['seq']}  id={event['id'][:8]}")

    # Simulate the network-drop scenario: manually send event[2] again
    # as if the original response was lost and the producer is retrying.
    duplicate = events[2]
    producer.send(TOPIC, value=duplicate).get(timeout=5)
    print(f"\n  RETRY:  seq={duplicate['seq']}  id={duplicate['id'][:8]}"
          f"  ← simulated retry after 'lost' response")

    producer.flush()
    producer.close()

    print("\nNow consume and count: seq=2 should appear twice.")
    print("  docker exec -it redpanda rpk topic consume delivery.demo --brokers localhost:9092 "
          "--offset start --format '%v\\n' | jq .seq")


if __name__ == "__main__":
    main()
```

---

```bash
python producer_at_least_once.py
```

```bash
docker exec -it redpanda \
    rpk topic consume delivery.demo \
    --brokers localhost:9092 \
    --offset start \
    --format '%v\n' \
    | jq .seq
```

You will see: `0, 1, 2, 3, 4, 2` — the duplicate at the end. In a real pipeline
this would cause double-processing: the downstream watcher fires twice for the
same event, the SBOM scanner runs twice, deployment gates trigger twice.

---

## Part 3 — Idempotent Producer

Now enable idempotence. The configuration change is a single line.

Create `producer_idempotent.py`:

```python
#!/usr/bin/env python3
"""
Lab 10 — Idempotent producer.

enable_idempotence=True causes kafka-python-ng to set:
  - acks = 'all'                      (required for idempotence)
  - retries = float('inf')            (retry forever within delivery_timeout_ms)
  - max_in_flight_requests_per_connection = 1  (preserve ordering with retries)

The broker deduplicates using producer ID + sequence number.
A retried message with the same sequence number is discarded silently.
"""

import json
import uuid
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC     = "delivery.demo"


def make_event(name: str, seq: int) -> dict:
    return {"id": str(uuid.uuid4()), "name": name, "seq": seq}


def main():
    # Exactly-once at the producer side
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        enable_idempotence=True,
        # acks, retries, max_in_flight are automatically set correctly
        # by enable_idempotence=True — do not override them manually
        delivery_timeout_ms=30000,
        value_serializer=lambda v: json.dumps(v).encode(),
    )

    print("Producer config when idempotence is enabled:")
    print(f"  acks                              = all (auto-set)")
    print(f"  retries                           = inf (auto-set)")
    print(f"  max_in_flight_requests_per_conn   = 1   (auto-set)")
    print()

    events = [make_event("service-b", i) for i in range(5)]

    for event in events:
        future = producer.send(TOPIC, value=event)
        future.get(timeout=5)
        print(f"  SENT:   seq={event['seq']}  id={event['id'][:8]}")

    # Attempt the same simulated retry — with idempotence, the broker
    # will reject the duplicate based on the sequence number.
    # NOTE: true broker-level deduplication requires the SAME producer
    # session (same PID). Application-level re-sends with a new producer
    # instance get a new PID and are NOT deduplicated at the broker.
    # See the warning in Part 4.
    duplicate = events[2]
    future = producer.send(TOPIC, value=duplicate)
    future.get(timeout=5)
    print(f"\n  RETRY:  seq={duplicate['seq']}  id={duplicate['id'][:8]}"
          f"  ← broker will deduplicate this within the session")

    producer.flush()
    producer.close()

    print("\nConsume and count: seq=2 should appear only once.")
    print("  docker exec -it redpanda rpk topic consume delivery.demo --brokers localhost:9092 "
          "--offset start --format '%v\\n' | jq .seq")


if __name__ == "__main__":
    main()
```

Reset the topic first so you are working with a clean log:

```bash
docker exec -it redpanda \
    rpk topic delete delivery.demo
docker exec -it redpanda \
    rpk topic create delivery.demo --partitions 1 --replicas 1

python producer_idempotent.py

docker exec -it redpanda \
    rpk topic consume delivery.demo \
    --brokers localhost:9092 \
    --offset start \
    --format '%v\n' \
    | jq .seq
```

Result: `0, 1, 2, 3, 4` — no duplicate. The broker received the retry with the
same PID and sequence number and discarded it silently.

---

## Part 4 — The Session Boundary: What Idempotence Does Not Cover

This is the most important concept in the lab. Idempotence is **within a single
producer session**. When a producer process restarts, it gets a new producer ID
(PID). The broker has no way to connect the new PID to the old one. If the old
producer sent a message and died before confirming it, and the new producer
re-sends it, the broker sees it as a new message from a new producer and accepts
it.

---

Demonstrate this:

```python
#!/usr/bin/env python3
"""
Lab 10 — Session boundary demonstration.

Two separate producer instances = two separate PIDs.
The broker cannot deduplicate across them.
This is the scenario that transactional producers solve.
"""

import json
import uuid
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC     = "delivery.demo"


def make_event(name: str, seq: int) -> dict:
    return {"id": str(uuid.uuid4()), "name": name, "seq": seq}


def send_with_new_producer(event: dict, label: str) -> None:
    """Each call creates a new producer = new session = new PID."""
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        enable_idempotence=True,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    producer.send(TOPIC, value=event).get(timeout=5)
    print(f"  {label}  seq={event['seq']}  id={event['id'][:8]}"
          f"  (new PID — broker cannot deduplicate)")
    producer.flush()
    producer.close()


def main():
    event = make_event("service-c", 99)

    # First "send" — producer crashes after broker accepts, before app confirms
    send_with_new_producer(event, "SEND 1:")

    # Application-level retry — new producer process, new PID
    # From the broker's perspective this is a brand new message
    send_with_new_producer(event, "RETRY: ")

    print("\nBoth sends landed. Same payload, different PIDs.")
    print("Idempotence only covers retries within one producer session.")
    print("For cross-session deduplication, use transactional producers.")


if __name__ == "__main__":
    main()
```

---

```bash
python session_boundary.py
```

```bash
docker exec -it redpanda \
    rpk topic consume delivery.demo \
    --brokers localhost:9092 \
    --offset start \
    --format '%v\n' \
    | jq 'select(.seq == 99) | .seq'
```

You will see `99` appear twice. Two producer sessions, two PIDs, no
deduplication.

---

## Part 5 — Transactional Producer

The transactional producer extends idempotence across sessions using a
`transactional_id` — a stable string you assign. When a producer starts with the
same `transactional_id` as a previous session, the broker fences the old session
and takes over. Any incomplete transaction from the old session is aborted. The
new session begins cleanly.

Transactions also add atomicity: you can send to multiple partitions or topics
and guarantee that either all messages commit or none do.

---

Create `producer_transactional.py`:

```python
#!/usr/bin/env python3
"""
Lab 10 — Transactional producer.

transactional_id provides:
  1. Cross-session idempotence — the broker fences old sessions
  2. Atomic multi-partition writes — all or nothing

Use when:
  - A producer process can restart and must not re-send committed messages
  - You write to multiple topics and need atomic commit across all of them
"""

import json
import uuid
from kafka import KafkaProducer
from kafka.errors import KafkaError

BOOTSTRAP      = "localhost:9092"
TOPIC          = "delivery.demo"
TRANSACTIONAL_ID = "epr-pipeline-producer-1"
# transactional_id must be unique per logical producer in your system.
# If you run two instances with the same ID, the broker fences the older one.


def make_event(name: str, seq: int) -> dict:
    return {"id": str(uuid.uuid4()), "name": name, "seq": seq}


def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        transactional_id=TRANSACTIONAL_ID,
        # enable_idempotence is automatically True when transactional_id is set
        value_serializer=lambda v: json.dumps(v).encode(),
    )

    # Must call init_transactions() before any transactional operations
    producer.init_transactions()
    print(f"Transactions initialized  (id={TRANSACTIONAL_ID})\n")

    # --- Transaction 1: normal commit ---
    print("=== Transaction 1: commit ===")
    producer.begin_transaction()
    try:
        for i in range(3):
            event = make_event("service-d", i)
            producer.send(TOPIC, value=event)
            print(f"  STAGED: seq={i}")
        producer.commit_transaction()
        print("  COMMITTED\n")
    except KafkaError as e:
        producer.abort_transaction()
        print(f"  ABORTED: {e}\n")

    # --- Transaction 2: simulate a processing error → abort ---
    print("=== Transaction 2: abort (simulated error mid-transaction) ===")
    producer.begin_transaction()
    try:
        event_ok  = make_event("service-d", 10)
        event_bad = make_event("service-d", 11)

        producer.send(TOPIC, value=event_ok)
        print(f"  STAGED: seq=10")

        # Something goes wrong before we finish
        raise ValueError("Downstream validation failed — rolling back")

        producer.send(TOPIC, value=event_bad)
        producer.commit_transaction()
    except (ValueError, KafkaError) as e:
        producer.abort_transaction()
        print(f"  ABORTED: {e}")
        print("  seq=10 will NOT appear in the committed log\n")

    # --- Transaction 3: commit after abort proves isolation ---
    print("=== Transaction 3: commit after abort ===")
    producer.begin_transaction()
    try:
        event = make_event("service-d", 20)
        producer.send(TOPIC, value=event)
        print(f"  STAGED: seq=20")
        producer.commit_transaction()
        print("  COMMITTED\n")
    except KafkaError as e:
        producer.abort_transaction()
        print(f"  ABORTED: {e}\n")

    producer.close()

    print("Expected committed sequence numbers: 0, 1, 2, 20")
    print("seq=10 was aborted and must not appear.\n")
    print("Verify with read_committed isolation:")
    print("  docker exec -it redpanda rpk topic consume delivery.demo --brokers localhost:9092 "
          "--offset start --format '%v\\n' | jq .seq")


if __name__ == "__main__":
    main()
```

---

```bash
docker exec -it redpanda \
    rpk topic delete delivery.demo
docker exec -it redpanda \
    rpk topic create delivery.demo --partitions 1 --replicas 1

python producer_transactional.py
```

---

### 5.1 Read with `read_committed` isolation

Without isolation level configuration, a consumer may read messages from aborted
transactions before they are marked as aborted. Always use `read_committed` when
consuming from topics written by transactional producers:

```python
#!/usr/bin/env python3
"""Lab 10 — Consumer with read_committed isolation."""

import json
from kafka import KafkaConsumer

BOOTSTRAP = "localhost:9092"
TOPIC     = "delivery.demo"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP,
    group_id="read-committed-demo",
    auto_offset_reset="earliest",
    isolation_level="read_committed",   # only see committed transactions
    consumer_timeout_ms=3000,
    value_deserializer=lambda b: json.loads(b.decode()),
)

print("Messages visible with read_committed:\n")
for record in consumer:
    print(f"  offset={record.offset}  seq={record.value.get('seq')}")

consumer.close()
```

---

```bash
python consumer_read_committed.py
```

You should see offsets for seq 0, 1, 2, and 20 — the two committed transactions.
The aborted seq=10 is not present. Without `isolation_level="read_committed"`,
you might briefly see it.

---

## Part 6 — Configuration Reference

### What `enable_idempotence=True` sets automatically

| Setting                                 | Value          | Why                                                  |
| --------------------------------------- | -------------- | ---------------------------------------------------- |
| `acks`                                  | `all`          | All in-sync replicas must acknowledge — no data loss |
| `retries`                               | `float('inf')` | Retry forever within `delivery_timeout_ms`           |
| `max_in_flight_requests_per_connection` | `1`            | Prevents reordering when retrying in-flight batches  |

Do not override these manually when idempotence is enabled. Setting `retries=0`
with `enable_idempotence=True` raises a `KafkaConfigurationError`.

---

### When to use each level

| You need                                      | Use                                           |
| --------------------------------------------- | --------------------------------------------- |
| Maximum throughput, can tolerate rare loss    | `acks=0` (fire and forget)                    |
| No loss, can tolerate rare duplicate          | `acks=all`, `retries>0`, no idempotence       |
| No loss, no duplicate within a session        | `enable_idempotence=True`                     |
| No loss, no duplicate across process restarts | `transactional_id=<stable-id>`                |
| Atomic write to multiple topics               | `transactional_id=<stable-id>` + transactions |

---

### The consumer-side requirement

Idempotence at the producer level does not protect against application-level
re-sends (calling `producer.send()` twice with the same payload from your code).
That is always a duplicate from the broker's perspective because it is a new
message with a new sequence number.

The full exactly-once story requires:

1. `enable_idempotence=True` on the producer — prevents duplicate broker writes
   on retry
2. `isolation_level=read_committed` on the consumer — prevents reading aborted
   transactions
3. Idempotent consumer logic — handles the residual duplicates that cross
   session boundaries

---

## Part 7 — Challenge Exercises

### Challenge A: Multi-topic atomic write

Modify `producer_transactional.py` to write to both `delivery.demo` and
`delivery.transactions` in a single transaction. Abort halfway through. Verify
that neither topic has the aborted messages by consuming both with
`read_committed` isolation.

---

### Challenge B: Producer epoch fencing

Run `producer_transactional.py` once to completion. Then modify it to simulate a
"zombie" scenario: start the producer, begin a transaction, then start a second
producer instance with the same `transactional_id` before the first commits.
Observe the `ProducerFencedException` that the first instance receives — this is
the broker fencing the old session to prevent the zombie from committing stale
data.

---

### Challenge C: Measure the cost of idempotence

Write a benchmark that produces 10,000 messages to a single-partition topic
three times:

- Without idempotence (`acks=1`)
- With idempotence (`enable_idempotence=True`)
- With transactions (`transactional_id=...`, one transaction per message)

Record throughput (messages/second) for each. The results should demonstrate
that idempotence is nearly free compared to no-idempotence `acks=all`, and that
per-message transactions are significantly more expensive than batched
transactions.

---

## Cleanup

```bash
docker exec -it redpanda \
    rpk topic delete delivery.demo delivery.transactions
```

---

**Duration:** ~55 minutes **Prerequisites:** Redpanda running via Docker
Compose; Python 3.12+ with `kafka-python-ng` installed.

---

## Key Takeaways

- Most pipelines claiming at-least-once actually have at-most-once because they
  lack `acks=all`. Verify your configuration.
- `enable_idempotence=True` is a single configuration change that upgrades
  at-least-once to exactly-once within a producer session. There is almost no
  throughput cost.
- Idempotence is per-session. A restarted producer gets a new PID. Cross-session
  deduplication requires `transactional_id`.
- Never override `acks`, `retries`, or `max_in_flight_requests_per_connection`
  manually when idempotence is enabled — let the client set them.
- Consumers reading from transactional topics must set
  `isolation_level=read_committed` or they may read messages from aborted
  transactions.
- Application-level re-sends (calling `producer.send()` twice from your own
  code) are never deduplicated — they are new messages to the broker regardless
  of idempotence settings.

---
