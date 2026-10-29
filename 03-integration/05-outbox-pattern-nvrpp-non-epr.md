# The Outbox Pattern and Provenance Tracing with NVRPP

## Overview

This lab covers two ideas that belong together.

The first is the **outbox pattern** — a solution to a fundamental reliability
problem that every event-driven system eventually hits. When a service writes to
a database and publishes to a message bus, those are two separate I/O
operations. A crash between them creates a silent gap in your event stream. No
error. No DLQ entry. No alert. Just a missing event, and a provenance chain with
a hole in it.

The second is **NVRPP** — Name, Version, Release, Platform ID, Package — the
five fields in every EPR event that together uniquely identify an artifact in
your pipeline. This lab makes the case that NVRPP is a better tracing primitive
for a provenance system than injecting UUID correlation IDs into Kafka headers,
and shows you how to query it.

These two ideas connect: the outbox pattern guarantees that every
database-committed build record eventually produces an EPR event, and NVRPP is
what makes those events queryable as a coherent provenance chain once they
arrive.

---

## Part 1 — The Problem: Dual Write Without Atomicity

### 1.1 The scenario

Your build service does two things when a build completes:

1. Inserts a row into the `build_records` PostgreSQL table
2. Publishes a `build.finished` event to the `epr.events` Redpanda topic

Here is the naive implementation that most teams start with:

```python
def record_build_naive(conn, producer, build: dict) -> None:
    """
    The naive approach. Works fine until it doesn't.
    """
    # Step 1: write to the database
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO build_records (id, name, version, release, platform_id, package,
                                       artifact_sha, repo, status, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW())
            """,
            (build["id"], build["name"], build["version"], build["release"],
             build["platform_id"], build["package"], build["artifact_sha"],
             build["repo"], build["status"]),
        )
    conn.commit()

    # Step 2: publish the event
    # *** THE PROCESS CAN CRASH RIGHT HERE ***
    # The row is committed. The event has not been sent.
    # Nothing will ever retry this publish.
    producer.send("epr.events", value=json.dumps(build).encode())
    producer.flush()
```

The comment in the middle is where your pipeline breaks. There is no way to make
a database `COMMIT` and a Kafka `producer.send()` atomic. They are fundamentally
different systems. Any approach that calls them sequentially has this gap.

---

### 1.2 Reproduce the failure

Set up the database:

```bash
# Connect to PostgreSQL
docker exec -it <postgres_container> psql -U postgres -d epr
```

```sql
CREATE TABLE build_records (
    id           UUID PRIMARY KEY,
    name         TEXT NOT NULL,
    version      TEXT NOT NULL,
    release      TEXT NOT NULL,
    platform_id  TEXT NOT NULL,
    package      TEXT NOT NULL,
    artifact_sha TEXT NOT NULL,
    repo         TEXT NOT NULL,
    status       TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Create `naive_producer.py`:

```python
#!/usr/bin/env python3
"""
Demonstrates the dual-write gap by simulating a crash between
the database write and the Kafka publish.
"""

import json
import uuid
import psycopg2
from kafka import KafkaProducer

DB_DSN    = "host=localhost dbname=epr user=postgres password=postgres"
BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events"

def make_build(name: str, version: str) -> dict:
    return {
        "id":           str(uuid.uuid4()),
        "name":         name,
        "version":      version,
        "release":      "20250901.1",
        "platform_id":  "linux/amd64",
        "package":      "rpm",
        "artifact_sha": f"sha256:{'a' * 16}",
        "repo":         f"github.com/acme/{name}",
        "status":       "success",
    }

def record_build_naive(conn, producer, build: dict, simulate_crash: bool = False) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO build_records
               (id, name, version, release, platform_id, package, artifact_sha, repo, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (build["id"], build["name"], build["version"], build["release"],
             build["platform_id"], build["package"], build["artifact_sha"],
             build["repo"], build["status"]),
        )
    conn.commit()
    print(f"  DB COMMITTED:  {build['name']} {build['version']} id={build['id'][:8]}...")

    if simulate_crash:
        print(f"  *** SIMULATED CRASH — Kafka publish never happens ***")
        raise RuntimeError("Process crash between DB commit and Kafka publish")

    producer.send(TOPIC, value=json.dumps(build).encode())
    producer.flush()
    print(f"  KAFKA SENT:    {build['name']} {build['version']}")


def main():
    conn     = psycopg2.connect(DB_DSN)
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    builds = [
        make_build("service-a", "1.0.0"),
        make_build("service-b", "2.1.0"),
        make_build("service-c", "0.9.0"),  # this one will "crash"
        make_build("service-d", "1.5.0"),
    ]

    for i, build in enumerate(builds):
        crash = (i == 2)
        try:
            record_build_naive(conn, producer, build, simulate_crash=crash)
        except RuntimeError as e:
            print(f"  ERROR: {e}")

    conn.close()
    producer.close()

    print("\nNow check the discrepancy:")
    print("  psql: SELECT name, version FROM build_records ORDER BY created_at;")
    print("  rpk:  docker exec -it redpanda rpk topic consume epr.events --brokers localhost:9092 --offset start")
    print("  service-c will appear in the DB but NOT in Kafka.")


if __name__ == "__main__":
    main()
```

---

```bash
python naive_producer.py
```

Then verify the gap:

```bash
# Four rows in the database
docker exec -it <postgres_container> psql -U postgres -d epr \
  -c "SELECT name, version, status FROM build_records ORDER BY created_at;"

# Three events in Kafka — service-c is missing
docker exec -it redpanda \
    rpk topic consume epr.events \
    --brokers localhost:9092 \
    --offset start \
    --format '%v\n' \
    | jq '.name + " " + .version'
```

`service-c 0.9.0` committed to the database. Never appeared in Kafka. Every
downstream system — your watcher, your SBOM scanner, your deployment gate — will
never know this build happened. The provenance chain has a silent gap.

---

## Part 2 — The Solution: The Outbox Pattern

### 2.1 The core idea

The outbox pattern eliminates the gap by making the Kafka event a side-effect of
the database transaction, not a separate operation after it.

Instead of:

```text
1. INSERT into build_records  ← commit
2. producer.send() to Kafka   ← separate, can fail
```

You do:

```text
1. INSERT into build_records  ┐
   INSERT into outbox         ┘ ← single commit, both or neither
2. Relay process reads outbox → publishes to Kafka → marks published
```

The database becomes the authoritative queue. If the service crashes before the
relay runs, the relay will publish on its next pass. If the relay crashes after
publishing but before marking the row as published, it re-publishes on restart —
which means consumers must handle duplicate events, but no events are ever
silently lost.

---

### 2.2 Create the outbox table

```sql
CREATE TABLE outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic           TEXT        NOT NULL,
    event_key       TEXT,
    payload         JSONB       NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at    TIMESTAMPTZ,
    published       BOOLEAN     NOT NULL DEFAULT FALSE,
    retry_count     INTEGER     NOT NULL DEFAULT 0,
    last_error      TEXT
);

CREATE INDEX idx_outbox_unpublished ON outbox (created_at)
    WHERE published = FALSE;
```

The index on `published = FALSE` with `created_at` ordering is important — the
relay will run this query frequently, and you only want it scanning the
unpublished rows.

---

### 2.3 Build service with outbox write

Create `build_service.py`:

```python
#!/usr/bin/env python3
"""
Build service using the outbox pattern.
The database transaction commits both the build record AND the outbox entry.
The Kafka publish happens in a separate relay process.
"""

import json
import uuid
import psycopg2
import psycopg2.extras

DB_DSN = "host=localhost dbname=epr user=postgres password=postgres"
TOPIC  = "epr.events"


def make_build(name: str, version: str, status: str = "success") -> dict:
    return {
        "id":           str(uuid.uuid4()),
        "type":         "build.finished",
        "name":         name,
        "version":      version,
        "release":      "20250901.1",
        "platform_id":  "linux/amd64",
        "package":      "rpm",
        "artifact_sha": f"sha256:{'b' * 16}",
        "repo":         f"github.com/acme/{name}",
        "status":       status,
    }


def record_build(conn, build: dict, simulate_crash_after_db: bool = False) -> None:
    """
    Writes business data and outbox entry in a single transaction.
    Either both are committed, or neither is.
    """
    with conn:
        with conn.cursor() as cur:
            # Business write
            cur.execute(
                """INSERT INTO build_records
                   (id, name, version, release, platform_id, package, artifact_sha, repo, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (build["id"], build["name"], build["version"], build["release"],
                 build["platform_id"], build["package"], build["artifact_sha"],
                 build["repo"], build["status"]),
            )

            # Outbox write — same transaction
            cur.execute(
                """INSERT INTO outbox (topic, event_key, payload)
                   VALUES (%s, %s, %s)""",
                (TOPIC, build["name"], json.dumps(build)),
            )

    # Transaction committed — both rows exist or neither does.
    print(f"  COMMITTED:  {build['name']} {build['version']} → build_records + outbox")

    if simulate_crash_after_db:
        print(f"  *** SIMULATED CRASH — but outbox row exists, relay will publish later ***")
        raise RuntimeError("Crash after commit — outbox entry safe in database")


def main():
    conn = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()

    builds = [
        make_build("service-a", "1.0.1"),
        make_build("service-b", "2.1.1"),
        make_build("service-c", "0.9.1"),  # will "crash" after commit
        make_build("service-d", "1.5.1"),
    ]

    for i, build in enumerate(builds):
        crash = (i == 2)
        try:
            record_build(conn, build, simulate_crash_after_db=crash)
        except RuntimeError as e:
            print(f"  (crash noted: {e})")
            print(f"  The outbox entry for service-c IS committed — relay will handle it.")

    conn.close()
    print("\nAll four rows in outbox. Run the relay to publish them.")


if __name__ == "__main__":
    main()
```

---

```bash
python build_service.py
```

Verify all four outbox rows exist, including service-c:

```sql
SELECT event_key, published, created_at
FROM outbox
ORDER BY created_at;
```

All four rows present. None yet published. The crash happened after the commit —
the data is safe.

---

### 2.4 Build the relay

The relay is a separate process. It polls the outbox for unpublished rows,
publishes each one to Kafka, then marks the row as published. It runs
continuously in the background.

Create `outbox_relay.py`:

```python
#!/usr/bin/env python3
"""
Outbox relay — reads unpublished outbox rows, publishes to Redpanda,
marks as published. Runs as a long-lived background process.

Guarantees: at-least-once delivery.
Consumers must be idempotent (deduplicate on NVRPP).
"""

import json
import time
import logging
import psycopg2
import psycopg2.extras
from kafka import KafkaProducer
from kafka.errors import KafkaError

DB_DSN      = "host=localhost dbname=epr user=postgres password=postgres"
BOOTSTRAP   = "localhost:9092"
POLL_INTERVAL = 2.0   # seconds between polls
BATCH_SIZE    = 50    # rows per poll cycle
MAX_RETRIES   = 5     # give up after this many publish failures

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("relay")


def fetch_unpublished(conn, batch_size: int) -> list[dict]:
    """
    Fetch a batch of unpublished outbox rows, oldest first.
    Uses SELECT FOR UPDATE SKIP LOCKED so multiple relay instances
    can run safely without processing the same row twice.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, topic, event_key, payload, retry_count
            FROM   outbox
            WHERE  published = FALSE
            AND    retry_count < %s
            ORDER  BY created_at
            LIMIT  %s
            FOR UPDATE SKIP LOCKED
            """,
            (MAX_RETRIES, batch_size),
        )
        return cur.fetchall()


def mark_published(conn, row_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE outbox SET published=TRUE, published_at=NOW() WHERE id=%s",
            (row_id,),
        )
    conn.commit()


def mark_failed(conn, row_id: str, error: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE outbox
               SET retry_count = retry_count + 1,
                   last_error  = %s
               WHERE id = %s""",
            (error[:500], row_id),
        )
    conn.commit()


def run_relay(conn, producer: KafkaProducer) -> None:
    rows = fetch_unpublished(conn, BATCH_SIZE)

    if not rows:
        return

    log.info(f"Processing {len(rows)} unpublished row(s)")

    for row in rows:
        try:
            future = producer.send(
                row["topic"],
                key=row["event_key"].encode() if row["event_key"] else None,
                value=row["payload"] if isinstance(row["payload"], bytes)
                      else json.dumps(row["payload"]).encode(),
            )
            future.get(timeout=10)
            mark_published(conn, row["id"])
            log.info(f"  PUBLISHED  {row['event_key']}  →  {row['topic']}")

        except KafkaError as e:
            log.warning(f"  FAILED     {row['event_key']}  retry={row['retry_count']+1}  {e}")
            mark_failed(conn, row["id"], str(e))

        except Exception as e:
            log.error(f"  ERROR      {row['event_key']}  {e}")
            mark_failed(conn, row["id"], str(e))


def main():
    log.info("Outbox relay starting")

    conn = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        acks="all",           # wait for all replicas to acknowledge
        retries=3,
        linger_ms=5,
    )

    log.info(f"Connected to DB and Redpanda. Polling every {POLL_INTERVAL}s")

    try:
        while True:
            run_relay(conn, producer)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log.info("Shutting down relay")
    finally:
        producer.close()
        conn.close()


if __name__ == "__main__":
    main()
```

---

Run the relay in a second terminal:

```bash
python outbox_relay.py
```

Watch it publish all four rows — including service-c that "crashed" earlier:

```text
09:14:01  INFO     Processing 4 unpublished row(s)
09:14:01  INFO       PUBLISHED  service-a  →  epr.events
09:14:01  INFO       PUBLISHED  service-b  →  epr.events
09:14:01  INFO       PUBLISHED  service-c  →  epr.events
09:14:01  INFO       PUBLISHED  service-d  →  epr.events
```

---

Verify in Kafka — all four now present:

```bash
docker exec -it redpanda \
    rpk topic consume epr.events \
    --brokers localhost:9092 \
    --offset start \
    --format '%v\n' \
    | jq '.name + " " + .version'
```

And the outbox table confirms completion:

```sql
SELECT event_key, published, published_at, retry_count
FROM outbox
ORDER BY created_at;
```

---

### 2.5 Understand what "at-least-once" means here

The outbox pattern guarantees every committed database row will eventually
produce a Kafka event. It does not guarantee exactly one event per row. If the
relay publishes to Kafka successfully but crashes before calling
`mark_published()`, it will re-publish the same row on its next run.

This means your consumers must handle duplicates. The correct tool is
idempotency keyed on NVRPP — which the next part of this lab addresses directly.

---

## Part 3 — NVRPP: Why Your Provenance Key Is Better Than a UUID

### 3.1 What a UUID in a Kafka header actually tells you

Many event-driven systems propagate a `correlation-id` or `trace-id` UUID
through message headers. The theory is: you can follow a UUID from service A
through service B through service C and reconstruct the full journey.

In practice, for a CI/CD provenance system, this breaks down in four ways.

First, **a UUID identifies a message instance, not an artifact.** If you replay
a topic — for recovery, for a new consumer catching up, for a schema migration —
every replayed message has the same UUID as the original. The UUID says nothing
about what artifact it refers to. NVRPP says exactly what artifact it refers to.

---

Second, **the UUID trace requires an external index.** To answer "what happened
to service-a 1.2.3?" using UUID tracing, you need some mapping from that build's
UUID to its downstream events. That mapping either lives in a separate service
(another thing to keep consistent) or you search Kafka for UUID matches (slow,
doesn't scale). With NVRPP, you query EPR directly:
`WHERE name='service-a' AND version='1.2.3'`.

---

Third, **UUIDs don't survive process boundaries cleanly.** If a build produces
ten artifacts — RPM, DEB, OCI image, source tarball — each is a separate EPR
event with its own NVRPP identity. A single UUID header cannot correlate across
those unless you build a separate fan-out correlation table. NVRPP correlates
them naturally: same name, same version, same release, different
platform_id/package.

---

Fourth, **UUIDs break on rebuild.** If service-a 1.2.3 is rebuilt from the same
source because the first build had an infrastructure failure, it gets a new
UUID. But NVRPP is the same — it is the same artifact at the same version. A
UUID-based trace now shows two disconnected traces for what is logically the
same thing. NVRPP shows both builds as entries in the same artifact's provenance
history, which is exactly what you want for audit purposes.

---

### 3.2 NVRPP as a natural compound key

The five NVRPP fields together answer the question: "what exactly is this
thing?"

| Field         | What it pins down                                  |
| ------------- | -------------------------------------------------- |
| `name`        | Which component                                    |
| `version`     | Which semantic release of the component            |
| `release`     | Which specific build attempt (date + build number) |
| `platform_id` | Which OS/architecture target                       |
| `package`     | Which packaging format                             |

`service-a / 1.2.3 / 20250901.1 / linux/amd64 / rpm` is unambiguous. It
describes exactly one artifact. Every EPR event for that artifact carries all
five fields. You can reconstruct the entire pipeline history for that artifact
by querying EPR with those five fields, in order by `created_at`.

No headers. No external index. No UUID mapping table. The provenance chain is
implicit in the data itself.

---

### 3.3 Query the provenance chain

Create `provenance_query.py`:

```python
#!/usr/bin/env python3
"""
Query the complete provenance chain for an artifact using NVRPP.
No UUIDs required. No Kafka header inspection required.
"""

import psycopg2
import psycopg2.extras
from datetime import datetime

DB_DSN = "host=localhost dbname=epr user=postgres password=postgres"


def get_provenance_chain(
    conn,
    name: str,
    version: str,
    release: str,
    platform_id: str,
    package: str,
) -> list[dict]:
    """
    Return all EPR events for an artifact, ordered by pipeline stage.
    This is the complete provenance chain.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT type, status, artifact_sha, repo, created_at
            FROM   build_records
            WHERE  name        = %s
            AND    version     = %s
            AND    release     = %s
            AND    platform_id = %s
            AND    package     = %s
            ORDER  BY created_at ASC
            """,
            (name, version, release, platform_id, package),
        )
        return [dict(row) for row in cur.fetchall()]


def format_chain(chain: list[dict], nvrpp: dict) -> None:
    print(f"\nProvenance chain for:")
    print(f"  name={nvrpp['name']}  version={nvrpp['version']}  "
          f"release={nvrpp['release']}")
    print(f"  platform_id={nvrpp['platform_id']}  package={nvrpp['package']}")
    print()

    if not chain:
        print("  (no events found)")
        return

    for i, event in enumerate(chain):
        ts = event["created_at"].strftime("%H:%M:%S.%f")[:12]
        print(f"  [{i+1}] {ts}  {event['type']:<25}  status={event['status']}")

    types = {e["type"] for e in chain}
    print(f"\n  Summary: {len(chain)} pipeline stage(s) recorded")
    if "build.finished" in types and "test.passed" in types:
        print("  Build and tests: confirmed")
    if "sbom.created" in types:
        print("  SBOM: confirmed")
    if "deploy.finished" in types:
        print("  Deployment: confirmed")
    else:
        print("  Deployment: not yet recorded")


def check_idempotency(conn, name: str, version: str, release: str,
                      platform_id: str, package: str) -> None:
    """
    Detect duplicate outbox-delivered events.
    With at-least-once delivery, the same NVRPP event might appear twice.
    This query surfaces that so consumers can deduplicate.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT type, COUNT(*) as count
            FROM   build_records
            WHERE  name        = %s
            AND    version     = %s
            AND    release     = %s
            AND    platform_id = %s
            AND    package     = %s
            GROUP  BY type
            HAVING COUNT(*) > 1
            """,
            (name, version, release, platform_id, package),
        )
        duplicates = cur.fetchall()

    if duplicates:
        print(f"\n  DUPLICATES DETECTED (at-least-once delivery):")
        for dup in duplicates:
            print(f"    {dup['type']} appeared {dup['count']} times — deduplicate on NVRPP")
    else:
        print(f"\n  No duplicates. Each pipeline stage recorded exactly once.")


def main():
    conn = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()

    # Query using NVRPP — no UUID needed
    nvrpp_targets = [
        {
            "name": "service-a", "version": "1.0.1",
            "release": "20250901.1", "platform_id": "linux/amd64", "package": "rpm",
        },
        {
            "name": "service-c", "version": "0.9.1",
            "release": "20250901.1", "platform_id": "linux/amd64", "package": "rpm",
        },
        # This one was in the naive test and never got a Kafka event — should show nothing
        {
            "name": "service-c", "version": "0.9.0",
            "release": "20250901.1", "platform_id": "linux/amd64", "package": "rpm",
        },
    ]

    for nvrpp in nvrpp_targets:
        chain = get_provenance_chain(conn, **nvrpp)
        format_chain(chain, nvrpp)
        check_idempotency(conn, **nvrpp)
        print()

    conn.close()


if __name__ == "__main__":
    main()
```

---

```bash
python provenance_query.py
```

Notice:

- `service-a 1.0.1` and `service-c 0.9.1` (from the outbox run) have complete
  entries.
- `service-c 0.9.0` (from the naive run that crashed) exists in the database but
  its event was never published — visible as a database record but missing from
  the event stream. This is the gap the outbox pattern prevents.

---

### 3.4 The idempotent consumer

Because the outbox relay delivers at-least-once, consumers must deduplicate. The
correct deduplication key is NVRPP + event type. If you see `build.finished` for
`service-a / 1.2.3 / 20250901.1 / linux/amd64 / rpm` twice, the second one is a
duplicate and should be skipped.

Add this to your EPR consumer pattern:

```python
def is_duplicate(conn, event: dict) -> bool:
    """
    Check whether this NVRPP + event type has already been processed.
    Used by consumers to handle at-least-once delivery from the outbox relay.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM processed_events
            WHERE name        = %s
            AND   version     = %s
            AND   release     = %s
            AND   platform_id = %s
            AND   package     = %s
            AND   event_type  = %s
            LIMIT 1
            """,
            (event["name"], event["version"], event["release"],
             event["platform_id"], event["package"], event["type"]),
        )
        return cur.fetchone() is not None


def mark_processed(conn, event: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO processed_events
                (name, version, release, platform_id, package, event_type, processed_at)
            VALUES (%s,%s,%s,%s,%s,%s, NOW())
            ON CONFLICT DO NOTHING
            """,
            (event["name"], event["version"], event["release"],
             event["platform_id"], event["package"], event["type"]),
        )
    conn.commit()
```

The `ON CONFLICT DO NOTHING` handles the race condition where two consumer
instances try to mark the same event simultaneously. Create the table to support
this:

```sql
CREATE TABLE processed_events (
    name        TEXT NOT NULL,
    version     TEXT NOT NULL,
    release     TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    package     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (name, version, release, platform_id, package, event_type)
);
```

The primary key is NVRPP + event type. That composite key IS the deduplication
mechanism. No UUID column. No correlation ID column. Just the five fields that
uniquely describe an artifact, plus the event type that describes what happened
to it.

---

## Part 4 — Putting It Together: Full Pipeline Simulation

Simulate a complete EPR pipeline for two services going through build → test →
SBOM → deploy, all using the outbox pattern, then query the complete provenance
chain for each.

Create `full_pipeline.py`:

```python
#!/usr/bin/env python3
"""
Full pipeline simulation using outbox pattern.
Demonstrates the complete provenance chain built from NVRPP events.
"""

import json
import uuid
import time
import threading
import psycopg2
import psycopg2.extras
from kafka import KafkaProducer
from kafka.errors import KafkaError

DB_DSN    = "host=localhost dbname=epr user=postgres password=postgres"
BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events"

PIPELINE_STAGES = [
    ("build.finished",  "success"),
    ("test.passed",     "success"),
    ("sbom.created",    "success"),
    ("deploy.started",  "pending"),
    ("deploy.finished", "success"),
]


def make_event(event_type: str, status: str, name: str, version: str,
               release: str = "20250901.2") -> dict:
    return {
        "id":           str(uuid.uuid4()),
        "type":         event_type,
        "name":         name,
        "version":      version,
        "release":      release,
        "platform_id":  "linux/amd64",
        "package":      "rpm",
        "artifact_sha": f"sha256:{'c' * 16}",
        "repo":         f"github.com/acme/{name}",
        "status":       status,
    }


def write_to_outbox(conn, event: dict) -> None:
    """Single-transaction write: business record + outbox entry."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO build_records
                   (id, name, version, release, platform_id, package,
                    artifact_sha, repo, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO NOTHING""",
                (event["id"], event["name"], event["version"], event["release"],
                 event["platform_id"], event["package"], event["artifact_sha"],
                 event["repo"], event["status"]),
            )
            cur.execute(
                "INSERT INTO outbox (topic, event_key, payload) VALUES (%s,%s,%s)",
                (TOPIC, f"{event['name']}-{event['type']}", json.dumps(event)),
            )
    print(f"  STAGED:  {event['name']} {event['version']} → {event['type']}")


def run_relay_once(conn, producer: KafkaProducer) -> int:
    """Run one relay cycle. Returns count of rows published."""
    published = 0
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """SELECT id, topic, event_key, payload FROM outbox
               WHERE published = FALSE ORDER BY created_at
               FOR UPDATE SKIP LOCKED"""
        )
        rows = cur.fetchall()

    for row in rows:
        try:
            producer.send(
                row["topic"],
                key=row["event_key"].encode(),
                value=json.dumps(row["payload"]).encode()
                       if not isinstance(row["payload"], (str, bytes))
                       else row["payload"].encode()
                            if isinstance(row["payload"], str)
                            else row["payload"],
            ).get(timeout=5)

            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE outbox SET published=TRUE, published_at=NOW() WHERE id=%s",
                    (row["id"],)
                )
            conn.commit()
            published += 1
        except KafkaError as e:
            print(f"  RELAY ERR: {e}")
            conn.rollback()

    return published


def print_provenance_chain(conn, name: str, version: str) -> None:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """SELECT type, status, created_at FROM build_records
               WHERE name=%s AND version=%s
               ORDER BY created_at""",
            (name, version),
        )
        rows = cur.fetchall()

    print(f"\n  Provenance chain: {name} {version}")
    for row in rows:
        ts = row["created_at"].strftime("%H:%M:%S")
        print(f"    {ts}  {row['type']:<25}  {row['status']}")


def main():
    conn     = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all")

    services = [
        ("service-alpha", "3.0.0"),
        ("service-beta",  "1.1.0"),
    ]

    print("=== Stage 1: Pipeline events written to outbox ===\n")
    for name, version in services:
        for event_type, status in PIPELINE_STAGES:
            event = make_event(event_type, status, name, version)
            write_to_outbox(conn, event)
            time.sleep(0.05)

    print(f"\n=== Stage 2: Relay publishes outbox to Redpanda ===\n")
    published = run_relay_once(conn, producer)
    print(f"  Published {published} events")

    print(f"\n=== Stage 3: Provenance chains (queried by NVRPP) ===")
    for name, version in services:
        print_provenance_chain(conn, name, version)

    producer.close()
    conn.close()


if __name__ == "__main__":
    main()
```

```bash
python full_pipeline.py
```

---

## Part 5 — Challenge Exercises

### Challenge A: Polling vs CDC

The relay in this lab uses polling — it runs a `SELECT` every few seconds. A
more production-grade approach is Change Data Capture (CDC): using PostgreSQL's
logical replication to stream outbox row insertions as a change stream,
eliminating the polling interval entirely. Research how `pg_logical` or Debezium
works and write a one-page design doc describing how you would replace the
polling relay with a CDC-based relay in the EPR pipeline.

---

### Challenge B: Multiple relay instances

The relay uses `SELECT FOR UPDATE SKIP LOCKED`, which means you can run multiple
relay instances safely — each one grabs a different set of rows. Start two
instances of `outbox_relay.py` simultaneously and produce a burst of 100 outbox
rows via `build_service.py`. Verify that all 100 rows are published exactly once
(no row published by both instances).

Hint: check `published_at` timestamps — two relays publishing the same row would
show a conflict error from the `UPDATE`.

---

### Challenge C: NVRPP cross-platform query

Modify `provenance_query.py` to query across all platforms for a given name +
version + release. Some components are built for `linux/amd64`, `linux/arm64`,
and `darwin/arm64`. Write a query that shows all platform variants of a release
side-by-side, including which platforms have completed deploy.finished and which
are still pending.

---

### Challenge D: Outbox TTL and archiving

Outbox rows for published events accumulate forever. Write a cleanup job
`outbox_cleanup.py` that:

1. Moves published outbox rows older than 7 days to an `outbox_archive` table
2. Deletes rows from `outbox_archive` older than 90 days
3. Reports how many rows were archived and deleted
4. Is safe to run concurrently with the relay

---

## Cleanup

```sql
DROP TABLE IF EXISTS outbox;
DROP TABLE IF EXISTS outbox_archive;
DROP TABLE IF EXISTS build_records;
DROP TABLE IF EXISTS processed_events;
```

```bash
docker exec -it redpanda \
    rpk topic delete epr.events
```

---

**Duration:** ~75 minutes **Prerequisites:** Labs 01–07 complete; PostgreSQL and
Redpanda running via Docker Compose; Python 3.12+ with `kafka-python-ng`,
`psycopg2-binary`, and `requests` installed.

---

## Key Takeaways

### On the outbox pattern

- A database `COMMIT` and a Kafka `producer.send()` can never be made atomic.
  Any code that calls them sequentially has a crash window.
- The outbox pattern closes that window by making the event a row in the same
  database transaction as the business data. The relay publishes it
  asynchronously.
- The outbox guarantees **at-least-once** delivery, not exactly-once. Consumers
  must be idempotent.
- `SELECT FOR UPDATE SKIP LOCKED` is the PostgreSQL primitive that makes
  multi-instance relays safe.
- The polling relay is simple and correct. CDC (Debezium, pg_logical) is faster
  and removes the polling interval but adds operational complexity. Start with
  polling.

---

### On NVRPP vs UUID headers

- A UUID traces a **message instance** through a message bus. NVRPP traces an
  **artifact** through a supply chain. These are different questions.
- To answer "what happened to service-a 1.2.3?" with UUID tracing, you need an
  external index from that UUID to the artifact's identity. With NVRPP, you
  query EPR directly.
- NVRPP is replay-proof. A replayed Kafka message has the same NVRPP it always
  had. A replayed message with a UUID header refers to the same artifact as the
  original.
- NVRPP is the natural deduplication key for idempotent consumers in an
  at-least-once system.
- The provenance chain is implicit in the EPR data model. You do not need to
  inject correlation infrastructure — the five NVRPP fields are the correlation
  infrastructure.

---

## Further Reading

- [Transactional Outbox Pattern — microservices.io](https://microservices.io/patterns/data/transactional-outbox.html)
- [PostgreSQL SELECT FOR UPDATE SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
- [Debezium — CDC for PostgreSQL](https://debezium.io/documentation/reference/connectors/postgresql.html)
- [Idempotent consumers in Kafka](https://docs.redpanda.com/current/develop/consume-data/consumer-offsets/)

---
