# Schema Registry with JSON Schema

## Overview

In previous labs you validated EPR event payloads manually inside consumer logic
— a hand-rolled `validate_event()` function that knew about required fields.
That works for a single team, but it breaks down the moment you have multiple
producers and consumers written by different people or deployed independently.
When the build service adds a field and the validator service doesn't know about
it, you get DLQ storms. When the validator service tightens a constraint and the
build service hasn't been updated, you get silent drops.

A **Schema Registry** solves this by making schemas a first-class artifact in
your pipeline — versioned, centrally stored, and enforced at both produce and
consume time. Producers register their schema before publishing. Consumers fetch
the schema before processing. Compatibility rules prevent breaking changes from
being registered at all.

Redpanda ships a built-in Schema Registry that is fully compatible with the
Confluent Schema Registry API. It runs alongside the broker with no additional
infrastructure.

---

### What you will learn

- How the Redpanda Schema Registry API works
- How to register, retrieve, and version JSON Schemas for EPR events
- How to enforce schema validation at produce time using the registry
- How to configure and test compatibility modes: `BACKWARD`, `FORWARD`, `FULL`,
  `NONE`
- How schema violations connect to the DLQ pattern from Lab 05

---

## Background: How the Schema Registry works

### The problem with inline validation

When schema knowledge lives in consumer code, every schema change requires a
coordinated deployment of all consumers before the producer can ship. In a CI/CD
pipeline with dozens of microservices this is operationally painful and
error-prone.

---

### The registry model

The Schema Registry stores schemas indexed by **subject**. The convention is:

```text
<topic-name>-value   →  schema for the message value
<topic-name>-key     →  schema for the message key (less common)
```

Each new schema registered under a subject gets an incremented **version
number**. Each schema also gets a globally unique **schema ID** across all
subjects.

```text
Subject: epr.events-value
  version 1  →  schema_id 1  →  { initial EPR event schema }
  version 2  →  schema_id 4  →  { added optional 'build_duration_ms' field }
  version 3  →  schema_id 9  →  { added required 'pipeline_id' field }
                                  ↑ this might be REJECTED depending on compat mode
```

---

### Compatibility modes

The registry enforces a **compatibility mode** per subject that controls what
schema changes are allowed:

| Mode                  | What it allows                                           | Use when                                                  |
| --------------------- | -------------------------------------------------------- | --------------------------------------------------------- |
| `BACKWARD`            | New schema can read data written by the previous schema  | Consumers deploy before producers                         |
| `FORWARD`             | Previous schema can read data written by the new schema  | Producers deploy before consumers                         |
| `FULL`                | Both backward and forward compatible                     | Zero-coordination deploys                                 |
| `BACKWARD_TRANSITIVE` | Compatible with all previous versions, not just the last | Long-lived consumers that may be multiple versions behind |
| `NONE`                | No compatibility checks                                  | Development / experimental topics                         |

For EPR's CI/CD pipeline, `BACKWARD` is the right default: consumers (watchers,
validators, storage services) are updated and deployed first, then the producer
(build service, CI runner) ships the new event fields.

---

## Part 1 — Verify Schema Registry

### 1.1 Check the Schema Registry is running

```bash
curl -s http://localhost:8081/ | jq .
```

You should see a response like:

```json
{}
```

A 200 with an empty body is healthy. If you get a connection refused, check your
Docker Compose setup — the Schema Registry port is `8081` by default in
Redpanda's Docker configuration.

---

### 1.2 List existing subjects

```bash
curl -s http://localhost:8081/subjects | jq .
```

At this point you should see an empty array `[]`.

---

### 1.3 Check global compatibility setting

```bash
curl -s http://localhost:8081/config | jq .
```

The default global compatibility is `BACKWARD`. You can override this per
subject.

---

### 1.4 Create the lab topic

```bash
docker exec -it redpanda \
    rpk topic create epr.events \
    --partitions 3 \
    --replicas 1
```

---

## Part 2 — Define and Register the Initial Schema

### 2.1 Understand the EPR event structure

From previous labs, a valid EPR event looks like this:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "build.finished",
  "artifact_sha": "sha256:abc123def456",
  "repo": "github.com/acme/service-a",
  "status": "success",
  "name": "service-a",
  "version": "1.2.3",
  "release": "20250901.1",
  "platform_id": "linux/amd64",
  "package": "rpm"
}
```

---

### 2.2 Create the initial schema file

Create `schemas/epr_event_v1.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://epr.example.com/schemas/event/v1",
  "title": "EPR Event",
  "description": "An event recorded in the Event Provenance Registry",
  "type": "object",
  "required": [
    "id",
    "type",
    "artifact_sha",
    "repo",
    "status",
    "name",
    "version",
    "release",
    "platform_id",
    "package"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique event identifier"
    },
    "type": {
      "type": "string",
      "enum": [
        "build.finished",
        "test.passed",
        "test.failed",
        "deploy.started",
        "deploy.finished",
        "sbom.created"
      ],
      "description": "Event type"
    },
    "artifact_sha": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{12,64}$",
      "description": "SHA256 digest of the artifact"
    },
    "repo": {
      "type": "string",
      "description": "Source repository"
    },
    "status": {
      "type": "string",
      "enum": ["success", "failure", "pending"],
      "description": "Outcome status"
    },
    "name": {
      "type": "string",
      "description": "Component name"
    },
    "version": {
      "type": "string",
      "description": "Semantic version"
    },
    "release": {
      "type": "string",
      "description": "Release identifier (e.g. build date + build number)"
    },
    "platform_id": {
      "type": "string",
      "description": "Target platform (e.g. linux/amd64)"
    },
    "package": {
      "type": "string",
      "description": "Package format (e.g. rpm, deb, oci)"
    }
  },
  "additionalProperties": false
}
```

> **Note on `additionalProperties: false`:** This is strict mode — any field not
> in the schema is rejected. During development you may want `true` to be
> permissive, but for a production provenance system where every field is
> auditable, strict mode is correct. Schema evolution (adding new fields) is the
> designed mechanism for growth.

---

### 2.3 Register the schema

```bash
# Register v1 of the EPR event schema
curl -s -X POST \
  http://localhost:8081/subjects/epr.events-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v1.json | jq -c .)}" \
  | jq .
```

You should receive:

```json
{
  "id": 1
}
```

That `id` is the globally unique schema ID. It never changes for this exact
schema, even if you re-register it.

---

### 2.4 Verify registration

```bash
# List subjects
curl -s http://localhost:8081/subjects | jq .

# Get the latest version
curl -s http://localhost:8081/subjects/epr.events-value/versions/latest | jq .

# Get just the schema body
curl -s http://localhost:8081/subjects/epr.events-value/versions/latest \
  | jq '.schema | fromjson'
```

---

### 2.5 Create a schema registry client module

Create `schema_registry.py` — a thin client you will reuse across the remaining
labs:

```python
"""
Thin client for the Redpanda Schema Registry (Confluent-compatible API).
Supports JSON Schema type. Does not use Avro.
"""

import json
import requests


class SchemaRegistryClient:
    def __init__(self, url: str = "http://localhost:8081"):
        self.url = url.rstrip("/")
        self._cache: dict[int, dict] = {}

    # ------------------------------------------------------------------ #
    # Registration                                                         #
    # ------------------------------------------------------------------ #

    def register(self, subject: str, schema: dict) -> int:
        """Register a JSON Schema under a subject. Returns the schema ID."""
        payload = {
            "schemaType": "JSON",
            "schema": json.dumps(schema),
        }
        resp = requests.post(
            f"{self.url}/subjects/{subject}/versions",
            json=payload,
            headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        )
        resp.raise_for_status()
        return resp.json()["id"]

    # ------------------------------------------------------------------ #
    # Retrieval                                                            #
    # ------------------------------------------------------------------ #

    def get_by_id(self, schema_id: int) -> dict:
        """Fetch a schema by its global ID. Results are cached."""
        if schema_id in self._cache:
            return self._cache[schema_id]
        resp = requests.get(f"{self.url}/schemas/ids/{schema_id}")
        resp.raise_for_status()
        schema = json.loads(resp.json()["schema"])
        self._cache[schema_id] = schema
        return schema

    def get_latest(self, subject: str) -> tuple[int, int, dict]:
        """
        Returns (schema_id, version, schema_dict) for the latest version
        of a subject.
        """
        resp = requests.get(f"{self.url}/subjects/{subject}/versions/latest")
        resp.raise_for_status()
        data = resp.json()
        schema = json.loads(data["schema"])
        return data["id"], data["version"], schema

    def get_version(self, subject: str, version: int) -> tuple[int, dict]:
        """Returns (schema_id, schema_dict) for a specific version."""
        resp = requests.get(f"{self.url}/subjects/{subject}/versions/{version}")
        resp.raise_for_status()
        data = resp.json()
        return data["id"], json.loads(data["schema"])

    def list_versions(self, subject: str) -> list[int]:
        """Returns all version numbers registered under a subject."""
        resp = requests.get(f"{self.url}/subjects/{subject}/versions")
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # Compatibility                                                        #
    # ------------------------------------------------------------------ #

    def set_compatibility(self, subject: str, mode: str) -> None:
        """Set compatibility mode for a subject. Mode must be one of:
        BACKWARD, FORWARD, FULL, BACKWARD_TRANSITIVE,
        FORWARD_TRANSITIVE, FULL_TRANSITIVE, NONE."""
        resp = requests.put(
            f"{self.url}/config/{subject}",
            json={"compatibility": mode},
            headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        )
        resp.raise_for_status()

    def check_compatibility(self, subject: str, schema: dict) -> bool:
        """
        Test whether a schema is compatible with the latest registered version
        of a subject, without registering it.
        Returns True if compatible.
        """
        payload = {"schemaType": "JSON", "schema": json.dumps(schema)}
        resp = requests.post(
            f"{self.url}/compatibility/subjects/{subject}/versions/latest",
            json=payload,
            headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        )
        resp.raise_for_status()
        return resp.json().get("is_compatible", False)
```

---

## Part 3 — Schema-Validated Producer

Now build a producer that fetches the schema from the registry before publishing
and validates each message locally before sending. Local validation catches
mistakes fast — you don't want to discover a malformed payload by watching DLQ
numbers climb.

Create `producer_validated.py`:

```python
#!/usr/bin/env python3
"""
Lab 06 producer — validates EPR events against the schema registry
before publishing to Redpanda.
"""

import json
import uuid
import time
from kafka import KafkaProducer
from jsonschema import validate, ValidationError
from schema_registry import SchemaRegistryClient

BOOTSTRAP = "localhost:9092"
TOPIC = "epr.events"
SUBJECT = "epr.events-value"

registry = SchemaRegistryClient()


def get_current_schema() -> tuple[int, dict]:
    schema_id, version, schema = registry.get_latest(SUBJECT)
    print(f"Using schema: subject={SUBJECT} version={version} id={schema_id}")
    return schema_id, schema


def make_event(event_type: str, name: str, version: str, **kwargs) -> dict:
    base = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "artifact_sha": f"sha256:{'a' * 12}",
        "repo": f"github.com/acme/{name}",
        "status": "success",
        "name": name,
        "version": version,
        "release": "20250901.1",
        "platform_id": "linux/amd64",
        "package": "rpm",
    }
    base.update(kwargs)
    return base


def main():
    schema_id, schema = get_current_schema()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    events = [
        make_event("build.finished", "service-a", "1.2.3"),
        make_event("test.passed",    "service-b", "0.9.1"),
        make_event("deploy.finished","service-a", "1.2.3"),
        # Intentionally broken: missing required 'package' field
        {
            "id": str(uuid.uuid4()),
            "type": "build.finished",
            "artifact_sha": "sha256:baddeadbeef",
            "repo": "github.com/acme/service-c",
            "status": "success",
            "name": "service-c",
            "version": "2.0.0",
            "release": "20250901.1",
            "platform_id": "linux/amd64",
            # 'package' is missing
        },
        # Intentionally broken: unknown event type
        make_event("build.exploded", "service-d", "1.0.0"),
    ]

    sent = rejected = 0

    for event in events:
        try:
            validate(instance=event, schema=schema)
        except ValidationError as e:
            print(f"  REJECTED (schema violation): {e.message}")
            rejected += 1
            continue

        future = producer.send(TOPIC, value=event)
        meta = future.get(timeout=5)
        print(f"  SENT → {meta.topic}:{meta.partition}@{meta.offset}  "
              f"type={event['type']} name={event['name']}")
        sent += 1
        time.sleep(0.05)

    producer.flush()
    producer.close()
    print(f"\nSent: {sent}  |  Rejected at producer: {rejected}")
    print(f"Schema ID used: {schema_id}  (embed this in message headers for traceability)")


if __name__ == "__main__":
    main()
```

---

Run it:

```bash
python producer_validated.py
```

Notice that the two broken events are rejected _before they touch the network_.
The DLQ never sees them. This is the first line of defence — catching schema
violations at the source.

---

## Part 4 — Schema-Aware Consumer

Build a consumer that fetches the schema from the registry at startup and
validates incoming messages. This provides defense-in-depth: even if a producer
skips local validation, the consumer catches it.

Create `consumer_schema_aware.py`:

```python
#!/usr/bin/env python3
"""
Lab 06 consumer — validates EPR events against the schema registry.
Invalid messages are routed to the DLQ with schema error metadata.
"""

import json
import datetime
from kafka import KafkaConsumer, KafkaProducer
from jsonschema import validate, ValidationError
from schema_registry import SchemaRegistryClient

BOOTSTRAP   = "localhost:9092"
SOURCE      = "epr.events"
DLQ         = "epr.events.dlq"
GROUP       = "epr-schema-validator-v1"
SUBJECT     = "epr.events-value"

registry = SchemaRegistryClient()


def send_to_dlq(producer, record, error: Exception, schema_id: int) -> None:
    headers = [
        ("dlq.original.topic",     SOURCE.encode()),
        ("dlq.original.partition", str(record.partition).encode()),
        ("dlq.original.offset",    str(record.offset).encode()),
        ("dlq.error.type",         type(error).__name__.encode()),
        ("dlq.error.message",      str(error)[:200].encode()),
        ("dlq.schema.id",          str(schema_id).encode()),
        ("dlq.schema.subject",     SUBJECT.encode()),
        ("dlq.timestamp",          datetime.datetime.utcnow().isoformat().encode()),
        ("dlq.consumer.group",     GROUP.encode()),
    ]
    producer.send(DLQ, key=record.key, value=record.value, headers=headers).get(timeout=5)
    print(f"    ✗ → DLQ  [{type(error).__name__}] {str(error)[:80]}")


def main():
    schema_id, version, schema = registry.get_latest(SUBJECT)
    print(f"Loaded schema: subject={SUBJECT} version={version} id={schema_id}\n")

    consumer = KafkaConsumer(
        SOURCE,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda b: b,
    )
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP)

    for record in consumer:
        print(f"  MSG  partition={record.partition} offset={record.offset}")
        try:
            event = json.loads(record.value.decode("utf-8"))
            validate(instance=event, schema=schema)
            print(f"    ✓ Valid: type={event.get('type')} "
                  f"name={event.get('name')} version={event.get('version')}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            send_to_dlq(producer, record, e, schema_id)
        except ValidationError as e:
            send_to_dlq(producer, record, e, schema_id)

        consumer.commit()

    consumer.close()
    producer.close()


if __name__ == "__main__":
    main()
```

---

Run it in a second terminal while the producer is running:

```bash
python consumer_schema_aware.py
```

---

## Part 5 — Compatibility Modes in Practice

This is where schema registry becomes genuinely powerful. You will register
three new versions of the EPR event schema and observe how compatibility mode
controls what is and is not allowed.

---

### 5.1 Set compatibility mode for the subject

```bash
# Set BACKWARD compatibility (the default, but explicit is better)
curl -s -X PUT \
  http://localhost:8081/config/epr.events-value \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"compatibility": "BACKWARD"}' \
  | jq .
```

---

### 5.2 Create a BACKWARD-compatible schema (adding an optional field)

A `BACKWARD`-compatible change means the new schema can still read data written
by the old schema. Adding an **optional** field is always backward compatible —
old messages simply won't have it, and the new schema accepts that.

Create `schemas/epr_event_v2.json` — adds an optional `build_duration_ms` field:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://epr.example.com/schemas/event/v2",
  "title": "EPR Event",
  "type": "object",
  "required": [
    "id",
    "type",
    "artifact_sha",
    "repo",
    "status",
    "name",
    "version",
    "release",
    "platform_id",
    "package"
  ],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "type": {
      "type": "string",
      "enum": [
        "build.finished",
        "test.passed",
        "test.failed",
        "deploy.started",
        "deploy.finished",
        "sbom.created"
      ]
    },
    "artifact_sha": { "type": "string", "pattern": "^sha256:[a-f0-9]{12,64}$" },
    "repo": { "type": "string" },
    "status": { "type": "string", "enum": ["success", "failure", "pending"] },
    "name": { "type": "string" },
    "version": { "type": "string" },
    "release": { "type": "string" },
    "platform_id": { "type": "string" },
    "package": { "type": "string" },
    "build_duration_ms": {
      "type": "integer",
      "minimum": 0,
      "description": "Build wall-clock time in milliseconds"
    }
  },
  "additionalProperties": false
}
```

---

Test compatibility before registering:

```bash
curl -s -X POST \
  "http://localhost:8081/compatibility/subjects/epr.events-value/versions/latest" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v2.json | jq -c .)}" \
  | jq .
```

Expected: `{"is_compatible": true}`

---

Register it:

```bash
curl -s -X POST \
  http://localhost:8081/subjects/epr.events-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v2.json | jq -c .)}" \
  | jq .
```

---

### 5.3 Attempt a BACKWARD-incompatible change (adding a required field)

Adding a **required** field breaks backward compatibility. Consumers using the
new schema cannot read old messages that lack the new required field.

Create `schemas/epr_event_v3_breaking.json` — adds a **required** `pipeline_id`
field:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://epr.example.com/schemas/event/v3-breaking",
  "title": "EPR Event",
  "type": "object",
  "required": [
    "id",
    "type",
    "artifact_sha",
    "repo",
    "status",
    "name",
    "version",
    "release",
    "platform_id",
    "package",
    "pipeline_id"
  ],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "type": {
      "type": "string",
      "enum": [
        "build.finished",
        "test.passed",
        "test.failed",
        "deploy.started",
        "deploy.finished",
        "sbom.created"
      ]
    },
    "artifact_sha": { "type": "string", "pattern": "^sha256:[a-f0-9]{12,64}$" },
    "repo": { "type": "string" },
    "status": { "type": "string", "enum": ["success", "failure", "pending"] },
    "name": { "type": "string" },
    "version": { "type": "string" },
    "release": { "type": "string" },
    "platform_id": { "type": "string" },
    "package": { "type": "string" },
    "build_duration_ms": { "type": "integer", "minimum": 0 },
    "pipeline_id": {
      "type": "string",
      "description": "CI pipeline identifier — REQUIRED, breaking change"
    }
  },
  "additionalProperties": false
}
```

---

Test compatibility — this should be rejected:

```bash
curl -s -X POST \
  "http://localhost:8081/compatibility/subjects/epr.events-value/versions/latest" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v3_breaking.json | jq -c .)}" \
  | jq .
```

---

Expected: `{"is_compatible": false}`

Attempt to register it anyway:

```bash
curl -s -X POST \
  http://localhost:8081/subjects/epr.events-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v3_breaking.json | jq -c .)}" \
  | jq .
```

Expected: a `409 Conflict` error. The registry refuses the registration. Your
pipeline is protected.

---

### 5.4 The correct way to add `pipeline_id`

Make it optional in v3. Producers can start populating it immediately; consumers
can start depending on it once all producers have been updated and old messages
have aged out of retention.

Create `schemas/epr_event_v3.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://epr.example.com/schemas/event/v3",
  "title": "EPR Event",
  "type": "object",
  "required": [
    "id",
    "type",
    "artifact_sha",
    "repo",
    "status",
    "name",
    "version",
    "release",
    "platform_id",
    "package"
  ],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "type": {
      "type": "string",
      "enum": [
        "build.finished",
        "test.passed",
        "test.failed",
        "deploy.started",
        "deploy.finished",
        "sbom.created"
      ]
    },
    "artifact_sha": { "type": "string", "pattern": "^sha256:[a-f0-9]{12,64}$" },
    "repo": { "type": "string" },
    "status": { "type": "string", "enum": ["success", "failure", "pending"] },
    "name": { "type": "string" },
    "version": { "type": "string" },
    "release": { "type": "string" },
    "platform_id": { "type": "string" },
    "package": { "type": "string" },
    "build_duration_ms": { "type": "integer", "minimum": 0 },
    "pipeline_id": {
      "type": "string",
      "description": "CI pipeline identifier — optional in v3, required in v4+"
    }
  },
  "additionalProperties": false
}
```

---

Verify and register:

```bash
curl -s -X POST \
  "http://localhost:8081/compatibility/subjects/epr.events-value/versions/latest" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v3.json | jq -c .)}" \
  | jq .
# Expected: {"is_compatible": true}

curl -s -X POST \
  http://localhost:8081/subjects/epr.events-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(cat schemas/epr_event_v3.json | jq -c .)}" \
  | jq .
# Expected: {"id": 3}
```

---

### 5.5 Inspect the version history

```bash
# List all versions
curl -s http://localhost:8081/subjects/epr.events-value/versions | jq .

# Diff v1 vs v3 — what changed?
echo "=== v1 required fields ==="
curl -s http://localhost:8081/subjects/epr.events-value/versions/1 \
  | jq '.schema | fromjson | .required'

echo "=== v3 properties ==="
curl -s http://localhost:8081/subjects/epr.events-value/versions/3 \
  | jq '.schema | fromjson | .properties | keys'
```

---

## Part 6 — Schema Evolution in Python

Build a small script that demonstrates the full producer + consumer lifecycle
across schema versions. Run the v1 producer, upgrade the consumer to use v3
schema, and confirm it can still read old messages.

Create `evolution_demo.py`:

```python
#!/usr/bin/env python3
"""
Lab 06 evolution demo.

Demonstrates that a consumer using schema v3 can successfully read
messages produced under schema v1 (backward compatibility).
"""

import json
import uuid
from kafka import KafkaProducer, KafkaConsumer
from jsonschema import validate, ValidationError
from schema_registry import SchemaRegistryClient

BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events.evolution-test"
SUBJECT   = "epr.events-value"

registry = SchemaRegistryClient()


def produce_v1_messages():
    """Produce messages that only contain v1 fields (no build_duration_ms, no pipeline_id)."""
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    _, _, v1_schema = registry.get_version(SUBJECT, 1)

    v1_events = [
        {
            "id": str(uuid.uuid4()),
            "type": "build.finished",
            "artifact_sha": "sha256:abc123def456",
            "repo": "github.com/acme/legacy-service",
            "status": "success",
            "name": "legacy-service",
            "version": "0.1.0",
            "release": "20240101.1",
            "platform_id": "linux/amd64",
            "package": "rpm",
        }
        for _ in range(3)
    ]

    for event in v1_events:
        validate(instance=event, schema=v1_schema)
        producer.send(TOPIC, value=event)
        print(f"  [PRODUCER v1] Sent: {event['name']} v{event['version']}")

    producer.flush()
    producer.close()


def produce_v3_messages():
    """Produce messages with all v3 fields populated."""
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    _, _, v3_schema = registry.get_latest(SUBJECT)

    v3_events = [
        {
            "id": str(uuid.uuid4()),
            "type": "build.finished",
            "artifact_sha": "sha256:def456abc789",
            "repo": "github.com/acme/new-service",
            "status": "success",
            "name": "new-service",
            "version": "1.0.0",
            "release": "20250901.1",
            "platform_id": "linux/amd64",
            "package": "oci",
            "build_duration_ms": 42000,
            "pipeline_id": "gh-actions-run-12345",
        }
        for _ in range(3)
    ]

    for event in v3_events:
        validate(instance=event, schema=v3_schema)
        producer.send(TOPIC, value=event)
        print(f"  [PRODUCER v3] Sent: {event['name']} v{event['version']} "
              f"pipeline={event.get('pipeline_id')}")

    producer.flush()
    producer.close()


def consume_with_v3_schema():
    """
    Consumer uses the latest (v3) schema.
    It must accept BOTH v1 messages (missing new optional fields)
    AND v3 messages (with new fields populated).
    """
    _, version, schema = registry.get_latest(SUBJECT)
    print(f"\n  [CONSUMER] Using schema v{version}")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="evolution-demo-consumer",
        auto_offset_reset="earliest",
        consumer_timeout_ms=3000,
        value_deserializer=lambda b: json.loads(b.decode()),
    )

    valid = invalid = 0
    for record in consumer:
        event = record.value
        try:
            validate(instance=event, schema=schema)
            has_pipeline = "pipeline_id" in event
            has_duration = "build_duration_ms" in event
            print(f"  [CONSUMER] ✓ {event['name']} v{event['version']} "
                  f"| pipeline_id={'yes' if has_pipeline else 'missing (v1 message)'} "
                  f"| build_duration={'yes' if has_duration else 'missing (v1 message)'}")
            valid += 1
        except ValidationError as e:
            print(f"  [CONSUMER] ✗ Validation failed: {e.message}")
            invalid += 1

    consumer.close()
    print(f"\n  Valid: {valid}  |  Invalid: {invalid}")
    print("  ↑ v1 messages validated successfully against v3 schema (backward compat working)")


def main():
    # Create test topic
    import subprocess
    subprocess.run(
        ["docker", "exec", "-it", "redpanda", "rpk", "topic", "create", TOPIC, "--partitions", "1", "--replicas", "1"],
        capture_output=True,
    )

    print("Step 1: Producing v1 messages (no new fields)...")
    produce_v1_messages()

    print("\nStep 2: Producing v3 messages (with new optional fields)...")
    produce_v3_messages()

    print("\nStep 3: Consuming all messages with v3 schema...")
    consume_with_v3_schema()


if __name__ == "__main__":
    main()
```

---

Run it:

```bash
python evolution_demo.py
```

The consumer reads all six messages — three v1 and three v3 — and validates them
all successfully against the v3 schema. This is backward compatibility working
as designed: adding optional fields lets consumers upgrade at their own pace
without breaking anything.

---

## Part 7 — Challenge Exercises

### Challenge A: FULL compatibility

Switch the subject's compatibility mode to `FULL` and try to register a schema
that removes a property. Observe the rejection. Then figure out the correct way
to deprecate a field under `FULL` compatibility (hint: it involves keeping the
field in the schema but documenting it as deprecated via a `description` change,
then removing it only after a full rotation).

```bash
curl -s -X PUT \
  http://localhost:8081/config/epr.events-value \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"compatibility": "FULL"}' | jq .
```

---

### Challenge B: Schema ID in message headers

Modify `producer_validated.py` to embed the schema ID in a Kafka message header
(`schema.id`). Modify `consumer_schema_aware.py` to read that header and fetch
the exact schema used at produce time instead of always using the latest
version. This lets the consumer validate each message against the schema it was
actually produced with — which matters when you're replaying historical messages
from a topic with long retention.

---

### Challenge C: New event type via enum evolution

The `type` field in the EPR schema uses `enum`. You need to add a new event
type: `"scan.completed"` for security scanning results. Try to add it under
`BACKWARD` mode. Does it work? Why or why not? (Hint: think about what happens
when an old consumer that only knows about the original enum values receives a
message with `"scan.completed"`.) Document your findings and propose the correct
migration strategy.

---

### Challenge D: Write a schema linter

Write a Python script `schema_lint.py` that takes a JSON Schema file as input
and checks it for common EPR-schema anti-patterns before registration:

- Fields without a `description`
- `additionalProperties` not explicitly set
- Enum fields with fewer than 2 values
- Required fields with no corresponding entry in `properties`

---

## Cleanup

```bash
docker exec -it redpanda \
    rpk topic delete epr.events epr.events.evolution-test

# Delete the subject from the schema registry (soft delete)
curl -s -X DELETE http://localhost:8081/subjects/epr.events-value | jq .

# Hard delete (permanent, removes all versions)
curl -s -X DELETE "http://localhost:8081/subjects/epr.events-value?permanent=true" | jq .
```

---

**Duration:** ~45 minutes **Prerequisites:** Labs 01–05 complete; Redpanda
running with Schema Registry enabled; Python 3.12+ with `kafka-python-ng`,
`jsonschema`, and `requests` installed.

---

## Key Takeaways

- The Schema Registry makes schemas a **versioned, centrally enforced contract**
  — not something buried in consumer code.
- **Compatibility mode is a deployment strategy**, not just a technical setting.
  `BACKWARD` means consumers deploy first; `FORWARD` means producers deploy
  first; `FULL` means either order works.
- **Test compatibility before registering**, not after. The
  `check_compatibility` endpoint is your schema CI gate.
- **Adding optional fields is always safe.** Adding required fields is always a
  breaking change unless you can guarantee all messages in retention already
  have that field.
- **Validate at the producer, validate at the consumer.** Defense in depth.
  Producer validation prevents bad data entering the pipeline; consumer
  validation protects against producers that skip local validation.
- The DLQ from Lab 05 and the schema registry form a complete error-handling
  system: the registry prevents most bad messages at source, and the DLQ catches
  the ones that slip through.

---
