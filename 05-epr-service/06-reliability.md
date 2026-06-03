# EPR Reliability Guarantees: Write-First, Replay, and NVRPP Provenance

**Duration:** ~60 minutes **Prerequisites:** EPR server, PostgreSQL, and
Redpanda running via Docker Compose; Python 3.10+ with `kafka-python-ng`,
`psycopg2-binary`, and `requests` installed.

---

## Overview

Most event-driven systems have a reliability problem they don't know about until
something goes wrong in production. A service writes to a database and publishes
to a message bus. Those are two separate I/O operations. A crash between them
creates a silent gap in the event stream — no error, no DLQ entry, no alert.
Just a missing event.

---

EPR's architecture makes this problem go away. The EPR server writes every event
to PostgreSQL _first_, returns a success response, and _then_ publishes to
Redpanda. The database is always the source of truth. Redpanda is a projection
of that truth onto a message bus.

---

This lab examines what that architecture buys you:

- Why write-first matters and what it protects against
- How to use EPR's PostgreSQL store as a recovery mechanism when Redpanda needs
  it
- How to replay events to new consumers without replaying an entire topic
- Why NVRPP makes all of the above queryable and targeted rather than blunt

This is not a lab about implementing a pattern. It is a lab about understanding
the guarantee EPR already gives you, and knowing how to use it.

---

## Background: The Dual-Write Problem EPR Solves For You

Consider the naive approach most services start with:

```text
1. INSERT into database    ← committed
2. producer.send() Kafka   ← separate operation, can fail silently
```

There is no way to make a database `COMMIT` and a Kafka `producer.send()`
atomic. They are different systems. Any code that calls them sequentially has a
crash window between step 1 and step 2. If the process dies there, the database
has a record that Kafka never heard about. No retry. No error. No recovery path.

---

EPR closes this window by inverting the responsibility:

```text
1. POST /events to EPR server
2. EPR: INSERT into PostgreSQL  ← committed
3. EPR: producer.send() Kafka   ← best-effort publish
4. EPR: return 200 to caller
```

---

From the caller's perspective, a 200 means the event is durably recorded. It is
in PostgreSQL. Whether or not the Redpanda publish succeeded in that moment is
secondary — EPR's database is the record of truth, and anything that needs to be
on the bus can be put there from the database.

The pattern that implements this formally — writing to an outbox table in the
same transaction as business data, then relaying to Kafka separately — is called
the Outbox Pattern. EPR _is_ that pattern, built into the server. You get it for
free.

---

## Part 1 — Observe the Write-First Architecture

### 1.1 Examine the EPR event write path

Look at how EPR handles a `POST /events` request. The key sequence in the EPR
server code is:

```go
// Simplified from the EPR server handler
func (s *Server) CreateEvent(ctx context.Context, req *CreateEventRequest) (*Event, error) {
    // Step 1: write to PostgreSQL — this is the durable commit
    event, err := s.store.CreateEvent(ctx, req)
    if err != nil {
        return nil, err  // DB write failed — return error, nothing published
    }

    // Step 2: publish to Redpanda — best-effort
    // If this fails, the event is still in the DB
    if err := s.producer.Publish(event); err != nil {
        s.logger.Warn("failed to publish event to message bus", "error", err)
        // Note: we do NOT return an error here. The event is durably stored.
        // The caller gets a 200. The event can be replayed from the DB.
    }

    return event, nil
}
```

The ordering is the guarantee. A caller who gets a 200 knows their event is in
PostgreSQL. The Redpanda publish is an optimistic best-effort on top of that.

---

### 1.2 Produce a set of pipeline events via EPR

Use the EPR API to record a complete pipeline run for `service-alpha`:

```bash
EPR_URL="http://localhost:8042"

# Build finished
curl -s -X POST $EPR_URL/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "name":         "service-alpha",
    "version":      "2.0.0",
    "release":      "20250901.1",
    "platform_id":  "linux/amd64",
    "package":      "rpm",
    "event_receiver_id": "<your-receiver-id>",
    "payload": {
      "type":         "build.finished",
      "artifact_sha": "sha256:abc123def456abc1",
      "repo":         "github.com/acme/service-alpha",
      "status":       "success"
    }
  }' | jq .

# Test passed
curl -s -X POST $EPR_URL/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "name":         "service-alpha",
    "version":      "2.0.0",
    "release":      "20250901.1",
    "platform_id":  "linux/amd64",
    "package":      "rpm",
    "event_receiver_id": "<your-receiver-id>",
    "payload": {
      "type":   "test.passed",
      "status": "success"
    }
  }' | jq .

# SBOM created
curl -s -X POST $EPR_URL/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "name":         "service-alpha",
    "version":      "2.0.0",
    "release":      "20250901.1",
    "platform_id":  "linux/amd64",
    "package":      "rpm",
    "event_receiver_id": "<your-receiver-id>",
    "payload": {
      "type":   "sbom.created",
      "status": "success"
    }
  }' | jq .
```

---

### 1.3 Verify both stores have the data

EPR's API (backed by PostgreSQL):

```bash
curl -s "$EPR_URL/api/v1/events?name=service-alpha&version=2.0.0" \
  | jq '[.[] | {type: .payload.type, created_at: .created_at}]'
```

---

Redpanda directly:

```bash
rpk topic consume epr.events \
  --brokers localhost:9092 \
  --offset start \
  --format '%v\n' \
  | jq 'select(.name == "service-alpha" and .version == "2.0.0") | .payload.type'
```

Both should show three events. The PostgreSQL record came first. The Redpanda
message is derived from it.

---

## Part 2 — Simulating a Redpanda Failure and Recovering

The point of write-first is that you can recover. This part proves it.

### 2.1 Simulate Redpanda being unavailable

Stop Redpanda while EPR is still running:

```bash
docker compose stop redpanda
```

---

### 2.2 Write events during the outage

EPR should still accept these — it can write to PostgreSQL without Redpanda:

```bash
curl -s -X POST $EPR_URL/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "name":         "service-alpha",
    "version":      "2.0.0",
    "release":      "20250901.1",
    "platform_id":  "linux/amd64",
    "package":      "rpm",
    "event_receiver_id": "<your-receiver-id>",
    "payload": {
      "type":   "deploy.started",
      "status": "pending"
    }
  }' | jq '{id: .id, created_at: .created_at}'

curl -s -X POST $EPR_URL/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "name":         "service-alpha",
    "version":      "2.0.0",
    "release":      "20250901.1",
    "platform_id":  "linux/amd64",
    "package":      "rpm",
    "event_receiver_id": "<your-receiver-id>",
    "payload": {
      "type":   "deploy.finished",
      "status": "success"
    }
  }' | jq '{id: .id, created_at: .created_at}'
```

Both should return 200 with event IDs. The events are in PostgreSQL. Redpanda
has no idea they exist yet.

---

### 2.3 Verify the gap

Bring Redpanda back:

```bash
docker compose start redpanda
```

---

Check Redpanda — it will be missing `deploy.started` and `deploy.finished`:

```bash
rpk topic consume epr.events \
  --brokers localhost:9092 \
  --offset start \
  --format '%v\n' \
  | jq 'select(.name == "service-alpha") | .payload.type'
```

---

Check EPR — all five events present:

```bash
curl -s "$EPR_URL/api/v1/events?name=service-alpha&version=2.0.0" \
  | jq '[.[] | .payload.type]'
```

This is the gap the write-first architecture protects you from losing. The
events exist. They are not gone. They need to be replayed onto the bus.

---

### 2.4 Replay missing events from EPR to Redpanda

Create `epr_replay.py`:

```python
#!/usr/bin/env python3
"""
Replays EPR events from PostgreSQL to Redpanda.
Use this to recover after a Redpanda outage, onboard a new consumer,
or backfill a new topic.

Replay is targeted by NVRPP — you replay exactly the artifact(s) you need,
not an entire topic.
"""

import json
import psycopg2
import psycopg2.extras
from kafka import KafkaProducer

DB_DSN    = "host=localhost dbname=epr user=postgres password=postgres"
BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events"


def fetch_events(
    conn,
    name: str,
    version: str,
    release: str,
    platform_id: str,
    package: str,
    since_id: str = None,
) -> list[dict]:
    """
    Fetch EPR events for a specific artifact (identified by NVRPP),
    optionally starting after a known event ID.

    `since_id` lets you replay only the events that came after the last
    one you know Redpanda received — avoiding re-publishing events that
    are already on the bus.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if since_id:
            cur.execute(
                """
                SELECT id, name, version, release, platform_id, package,
                       payload, created_at
                FROM   events
                WHERE  name        = %s
                AND    version     = %s
                AND    release     = %s
                AND    platform_id = %s
                AND    package     = %s
                AND    created_at > (
                    SELECT created_at FROM events WHERE id = %s
                )
                ORDER  BY created_at ASC
                """,
                (name, version, release, platform_id, package, since_id),
            )
        else:
            cur.execute(
                """
                SELECT id, name, version, release, platform_id, package,
                       payload, created_at
                FROM   events
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


def replay_to_redpanda(
    producer: KafkaProducer,
    events: list[dict],
    dry_run: bool = False,
) -> int:
    """
    Publish events to Redpanda. Returns count published.
    With dry_run=True, prints what would be published without sending.
    """
    published = 0
    for event in events:
        nvrpp_key = (
            f"{event['name']}/"
            f"{event['version']}/"
            f"{event['release']}/"
            f"{event['platform_id']}/"
            f"{event['package']}"
        )
        payload = {
            "id":          str(event["id"]),
            "name":        event["name"],
            "version":     event["version"],
            "release":     event["release"],
            "platform_id": event["platform_id"],
            "package":     event["package"],
            "payload":     event["payload"],
            "replayed":    True,   # mark as replay so consumers can detect it
            "created_at":  event["created_at"].isoformat(),
        }

        if dry_run:
            print(f"  [DRY RUN] would publish: {nvrpp_key} → {event['payload'].get('type')}")
        else:
            producer.send(
                TOPIC,
                key=nvrpp_key.encode(),
                value=json.dumps(payload).encode(),
            ).get(timeout=5)
            print(f"  REPLAYED: {nvrpp_key} → {event['payload'].get('type')}")
            published += 1

    return published


def main():
    conn     = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all")

    # The artifact we need to replay — identified by NVRPP
    target = {
        "name":        "service-alpha",
        "version":     "2.0.0",
        "release":     "20250901.1",
        "platform_id": "linux/amd64",
        "package":     "rpm",
    }

    print(f"Fetching events for: {target['name']} {target['version']}")
    print(f"  release={target['release']}  platform={target['platform_id']}  "
          f"package={target['package']}\n")

    events = fetch_events(conn, **target)
    print(f"Found {len(events)} event(s) in EPR database\n")

    # Dry run first — confirm what we're about to publish
    print("=== Dry run ===")
    replay_to_redpanda(producer, events, dry_run=True)

    print("\n=== Live replay ===")
    count = replay_to_redpanda(producer, events, dry_run=False)

    producer.flush()
    producer.close()
    conn.close()

    print(f"\nReplayed {count} event(s) to {TOPIC}")
    print("Consumers will see 'replayed: true' on these messages.")


if __name__ == "__main__":
    main()
```

---

```bash
python epr_replay.py
```

Verify Redpanda now has all five events:

```bash
rpk topic consume epr.events \
  --brokers localhost:9092 \
  --offset start \
  --format '%v\n' \
  | jq 'select(.name == "service-alpha") | {type: .payload.type, replayed: .replayed}'
```

---

The `"replayed": true` field lets consumers know these messages came from a
replay rather than live production. Idempotent consumers can use this as a
signal to skip side-effects they already performed (sending a Slack
notification, triggering a deployment) while still updating any local state that
needs the event.

---

## Part 3 — NVRPP as the Provenance Key

### 3.1 Why not inject a UUID correlation ID into headers?

The standard distributed tracing approach is to propagate a `correlation-id` or
`trace-id` UUID through message headers. This works well for tracing a request
through a web service call graph. For a CI/CD provenance system it is the wrong
tool, for four concrete reasons.

---

**A UUID identifies a message instance, not an artifact.** When you replay
events from EPR's database to Redpanda — as you just did — every replayed
message is a new Kafka message with a new offset. If you were using UUID headers
to link events to a build, those links are now broken. The replayed messages
have different Kafka offsets, different headers if you re-generated them, and a
UUID correlation from "before the outage" means nothing to "after the replay."
NVRPP is unchanged. `service-alpha / 2.0.0 / 20250901.1 / linux/amd64 / rpm` is
the same before and after replay, before and after any broker failure, before
and after any migration.

---

**UUID tracing requires an external index.** To answer "what happened to
service-alpha 2.0.0?" using UUID correlation, you need some mapping from that
build's UUID to its downstream events. Either you build a separate correlation
service, or you scan Kafka for matching UUIDs. Both are fragile. With NVRPP you
query EPR directly — five WHERE clauses, no secondary index, no UUID lookup.

---

**UUID links break across rebuilds.** If service-alpha 2.0.0 is rebuilt because
the first build had an infrastructure failure (not a code change), it gets a new
UUID. You now have two disconnected UUID traces for the same logical artifact.
NVRPP records both build attempts under the same identity — same name, version,
platform, package, but different release timestamps — which is exactly the right
representation for an audit trail.

---

**UUIDs require explicit propagation discipline.** Every service in the pipeline
must correctly read the UUID from the incoming message and write it to the
outgoing message. One service that forgets breaks the chain silently. NVRPP
requires no propagation — every EPR event carries the five fields independently
because they describe the artifact, not the message.

---

### 3.2 The provenance chain as a query

NVRPP makes the provenance chain a database query, not a graph traversal.

Create `provenance_query.py`:

```python
#!/usr/bin/env python3
"""
Query the complete provenance chain for an artifact using NVRPP.

Demonstrates that EPR's database gives you full pipeline history
with a simple SELECT — no UUID correlation, no header inspection,
no graph traversal.
"""

import psycopg2
import psycopg2.extras

DB_DSN = "host=localhost dbname=epr user=postgres password=postgres"


def provenance_chain(
    conn,
    name: str,
    version: str,
    release: str,
    platform_id: str,
    package: str,
) -> list[dict]:
    """
    Return all recorded pipeline events for an artifact, in order.
    This IS the provenance chain.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id,
                   payload->>'type'   AS event_type,
                   payload->>'status' AS status,
                   created_at
            FROM   events
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


def all_platforms(
    conn,
    name: str,
    version: str,
    release: str,
) -> list[dict]:
    """
    Return the pipeline status for ALL platform variants of a release.
    Answers: "which platforms have completed deployment, which haven't?"
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT   platform_id,
                     package,
                     array_agg(payload->>'type' ORDER BY created_at) AS stages,
                     MAX(created_at) AS last_event
            FROM     events
            WHERE    name    = %s
            AND      version = %s
            AND      release = %s
            GROUP BY platform_id, package
            ORDER BY platform_id, package
            """,
            (name, version, release),
        )
        return [dict(row) for row in cur.fetchall()]


def print_chain(chain: list[dict], nvrpp: dict) -> None:
    label = (f"{nvrpp['name']} {nvrpp['version']} "
             f"({nvrpp['platform_id']}/{nvrpp['package']})")
    print(f"\nProvenance chain: {label}")
    print(f"{'─' * 60}")

    if not chain:
        print("  No events recorded.")
        return

    for event in chain:
        ts = event["created_at"].strftime("%H:%M:%S")
        print(f"  {ts}  {event['event_type']:<25}  {event['status']}")

    types = [e["event_type"] for e in chain]
    print(f"\n  {len(chain)} stage(s) recorded")

    checks = [
        ("build.finished",  "Build"),
        ("test.passed",     "Tests"),
        ("sbom.created",    "SBOM"),
        ("deploy.finished", "Deploy"),
    ]
    for event_type, label in checks:
        mark = "✓" if event_type in types else "·"
        print(f"  {mark}  {label}")


def print_platform_summary(rows: list[dict], name: str, version: str, release: str) -> None:
    print(f"\nPlatform summary: {name} {version} ({release})")
    print(f"{'─' * 60}")

    if not rows:
        print("  No events recorded.")
        return

    for row in rows:
        deployed = "deploy.finished" in (row["stages"] or [])
        status   = "deployed" if deployed else "pending"
        stages   = " → ".join(row["stages"] or [])
        print(f"  {row['platform_id']:<18} {row['package']:<8}  "
              f"[{status}]  {stages}")


def main():
    conn = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()

    # Full chain for a specific platform variant
    nvrpp = {
        "name":        "service-alpha",
        "version":     "2.0.0",
        "release":     "20250901.1",
        "platform_id": "linux/amd64",
        "package":     "rpm",
    }
    chain = provenance_chain(conn, **nvrpp)
    print_chain(chain, nvrpp)

    # All platform variants of the same release
    rows = all_platforms(conn, "service-alpha", "2.0.0", "20250901.1")
    print_platform_summary(rows, "service-alpha", "2.0.0", "20250901.1")

    conn.close()


if __name__ == "__main__":
    main()
```

---

```bash
python provenance_query.py
```

---

### 3.3 The question NVRPP answers that UUID cannot

Read through these queries and notice what they have in common — none of them
mention Kafka, none of them require header inspection, and none of them need a
UUID:

```sql
-- What is the complete pipeline history for this artifact?
SELECT payload->>'type', payload->>'status', created_at
FROM   events
WHERE  name='service-alpha' AND version='2.0.0'
AND    release='20250901.1' AND platform_id='linux/amd64' AND package='rpm'
ORDER  BY created_at;

-- Which versions of service-alpha have been deployed to production?
SELECT DISTINCT version, release, platform_id, package
FROM   events
WHERE  name          = 'service-alpha'
AND    payload->>'type' = 'deploy.finished'
AND    payload->>'status' = 'success'
ORDER  BY release DESC;

-- Which builds from today have NOT yet had an SBOM created?
SELECT DISTINCT name, version, release, platform_id, package
FROM   events
WHERE  DATE(created_at) = CURRENT_DATE
AND    payload->>'type' = 'build.finished'
AND    (name, version, release, platform_id, package) NOT IN (
    SELECT name, version, release, platform_id, package
    FROM   events
    WHERE  payload->>'type' = 'sbom.created'
);

-- Has this specific artifact been through all required pipeline gates?
SELECT
    bool_or(payload->>'type' = 'build.finished')  AS built,
    bool_or(payload->>'type' = 'test.passed')      AS tested,
    bool_or(payload->>'type' = 'sbom.created')     AS sbom_scanned,
    bool_or(payload->>'type' = 'deploy.finished')  AS deployed
FROM events
WHERE name='service-alpha' AND version='2.0.0'
AND   release='20250901.1' AND platform_id='linux/amd64' AND package='rpm';
```

---

Run these against your EPR database. Each one is answerable because every event
carries NVRPP. The provenance chain is not constructed by following UUID links —
it is implicit in the data model. Every event for an artifact shares the same
five fields. A GROUP BY or WHERE clause on those fields assembles the chain.

---

## Part 4 — Consumer Idempotency Using NVRPP

Because EPR publishes to Redpanda on a best-effort basis and replay is possible,
consumers must handle seeing the same event more than once. The correct
deduplication key is NVRPP + event type — not the Kafka message offset, not a
UUID.

Create `idempotent_consumer.py`:

```python
#!/usr/bin/env python3
"""
EPR event consumer that deduplicates on NVRPP + event type.

Because EPR guarantees at-least-once delivery (write to DB first,
publish to Redpanda best-effort, replay possible), consumers must
be idempotent. NVRPP is the natural deduplication key.
"""

import json
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer

DB_DSN    = "host=localhost dbname=epr user=postgres password=postgres"
BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events"
GROUP     = "epr-idempotent-consumer-v1"


def setup_dedup_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS consumer_processed (
                name        TEXT NOT NULL,
                version     TEXT NOT NULL,
                release     TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                package     TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                was_replay   BOOLEAN NOT NULL DEFAULT FALSE,
                PRIMARY KEY (name, version, release, platform_id, package, event_type)
            )
            """
        )
    conn.commit()


def already_processed(conn, event: dict) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM consumer_processed
            WHERE name=%s AND version=%s AND release=%s
            AND   platform_id=%s AND package=%s AND event_type=%s
            """,
            (event["name"], event["version"], event["release"],
             event["platform_id"], event["package"],
             event.get("payload", {}).get("type", event.get("type"))),
        )
        return cur.fetchone() is not None


def mark_processed(conn, event: dict, was_replay: bool) -> None:
    event_type = event.get("payload", {}).get("type", event.get("type"))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO consumer_processed
                (name, version, release, platform_id, package, event_type, was_replay)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            (event["name"], event["version"], event["release"],
             event["platform_id"], event["package"], event_type, was_replay),
        )
    conn.commit()


def process_event(event: dict, was_replay: bool) -> None:
    """Your actual business logic goes here."""
    event_type = event.get("payload", {}).get("type", event.get("type", "unknown"))
    replay_tag = " [replay]" if was_replay else ""
    print(f"    ✓ Processing: {event['name']} {event['version']} "
          f"→ {event_type}{replay_tag}")


def main():
    conn = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_uuid()
    setup_dedup_table(conn)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=5000,
        value_deserializer=lambda b: json.loads(b.decode()),
    )

    processed = skipped = 0

    for record in consumer:
        event     = record.value
        was_replay = event.get("replayed", False)

        print(f"  MSG  offset={record.offset} "
              f"key={record.key.decode() if record.key else '-'}")

        if already_processed(conn, event):
            print(f"    · Duplicate (NVRPP match) — skipping"
                  f"{' replayed message' if was_replay else ''}")
            skipped += 1
        else:
            process_event(event, was_replay)
            mark_processed(conn, event, was_replay)
            processed += 1

        consumer.commit()

    consumer.close()
    conn.close()

    print(f"\nProcessed: {processed}  |  Skipped as duplicates: {skipped}")

    if skipped > 0:
        print(f"\nDuplicate breakdown:")
        with psycopg2.connect(DB_DSN) as c:
            with c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, version, event_type, was_replay "
                    "FROM consumer_processed ORDER BY processed_at"
                )
                for row in cur.fetchall():
                    tag = " (from replay)" if row["was_replay"] else ""
                    print(f"  {row['name']} {row['version']} "
                          f"→ {row['event_type']}{tag}")


if __name__ == "__main__":
    main()
```

---

Run it against the topic that now contains both the original three events and
the two replayed events:

```bash
python idempotent_consumer.py
```

The consumer processes each unique NVRPP + event type exactly once, regardless
of how many times that combination appears on the topic. The `was_replay` flag
lets you audit which processings came from replay vs live production — useful
for debugging and compliance reporting.

---

## Part 5 — Challenge Exercises

### Challenge A: Targeted replay by pipeline stage

Modify `epr_replay.py` to accept a `since_event_type` argument. Instead of
replaying all events for an artifact, replay only the events that came after a
specific stage. For example: replay everything after `test.passed` for
service-alpha 2.0.0. This is useful when a downstream consumer was unavailable
for the tail of a pipeline run and you need to replay only what it missed.

---

### Challenge B: Gap detection

Write `gap_detector.py` that compares EPR's database to Redpanda and reports any
events that are in the database but not on the bus. Do this by:

1. Fetching all events from EPR for the last 24 hours grouped by NVRPP
2. Consuming the Redpanda topic and building the same grouping
3. Reporting any NVRPP + event type combinations present in EPR but absent from
   Redpanda

This is the operational tool you would run after a Redpanda outage to identify
what needs replaying.

---

### Challenge C: Multi-release pipeline coverage report

Write a query that answers: "for the last 10 releases of any service, what
percentage reached `deploy.finished`?" Group by service name and show a coverage
rate per service. This demonstrates NVRPP as a reporting primitive, not just a
tracing primitive.

---

### Challenge D: Replay with consumer group reset

When you replay events to Redpanda, existing consumer groups that have already
committed offsets past the original messages will not re-consume the replayed
messages — they are appended to the end of the topic, so all consumer groups
will see them regardless of committed offset. Verify this is true by:

1. Running `idempotent_consumer.py` to process the original events (offsets
   committed)
2. Running `epr_replay.py` to append the replay
3. Running `idempotent_consumer.py` again

Confirm that the consumer sees the replayed messages (they are at new,
unconsumed offsets) but skips them as duplicates via the NVRPP deduplication
table. This is exactly the correct behavior.

---

## Cleanup

```sql
DROP TABLE IF EXISTS consumer_processed;
```

```bash
rpk topic delete epr.events
```

---

## Key Takeaways

### On EPR's write-first architecture

- EPR writes to PostgreSQL first, publishes to Redpanda second. A 200 response
  means the event is durably stored in the database — Redpanda is a projection
  of that truth, not the truth itself.
- This is the Outbox Pattern implemented inside the EPR server. You get it for
  free. You do not need to implement it yourself.
- If Redpanda is unavailable, events still accumulate in EPR's database. When
  Redpanda recovers, you replay from EPR — targeted, by NVRPP, only what is
  missing.

---

### On NVRPP as a provenance key

- NVRPP (Name, Version, Release, Platform ID, Package) identifies an artifact. A
  UUID identifies a message. These answer different questions.
- The provenance chain is implicit in EPR's data model. Every event for an
  artifact shares the same five NVRPP fields. No UUID correlation, no header
  propagation discipline, no secondary index required.
- NVRPP is replay-proof. A replayed message has the same NVRPP as the original.
  UUID-based correlation breaks on replay because the Kafka message is new even
  though the artifact is not.
- NVRPP is the correct deduplication key for idempotent consumers in an
  at-least-once system. The composite key
  `(name, version, release, platform_id, package, event_type)` is all you need.

---

### On the relationship between the two

- Write-first gives you the recovery mechanism. NVRPP gives you the targeting.
  Together they mean: after any failure, you can identify exactly which events
  are missing (by querying EPR with NVRPP) and replay exactly those events (by
  writing them back to Redpanda). No guessing. No full-topic replay. No UUID
  hunting.

---

## Further Reading

- [Transactional Outbox Pattern — microservices.io](https://microservices.io/patterns/data/transactional-outbox.html)
- [EPR project — github.com/xbcsmith/epr](https://github.com/xbcsmith/epr)
- [Redpanda topic replay — rpk topic consume --offset](https://docs.redpanda.com/current/reference/rpk/rpk-topic/rpk-topic-consume/)
- [PostgreSQL SELECT FOR UPDATE SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)

---
