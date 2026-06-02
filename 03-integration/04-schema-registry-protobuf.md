# Schema Registry with Protobuf

## Overview

The previous session used JSON Schema — human-readable, easy to write, no
compilation step. That's the right choice for getting started and for teams
primarily working in dynamic languages. Protobuf is the right choice when you
care about performance, strict typing across multiple languages, or generating
client code automatically from your schema.

In a CI/CD pipeline context, Protobuf makes sense when:

- Events are high-volume (thousands per second) and JSON parsing overhead is
  measurable
- You have consumers written in Go, Python, and Java that all need to agree on
  the exact same message structure
- You want generated, type-safe client libraries rather than hand-written
  validation logic
- Your EPR events are going to be forwarded to a gRPC service or stored in a
  columnar format

This lab walks through defining EPR events in `.proto` files, registering the
compiled schema with Redpanda's Schema Registry, and building producers and
consumers that use generated Python classes.

---

### What you will learn

- How to define EPR events in Protocol Buffers (proto3)
- How to compile `.proto` files and generate Python code with `protoc`
- How to register a Protobuf schema with the Redpanda Schema Registry
- How to produce and consume EPR events using generated Protobuf classes
- How Protobuf handles schema evolution differently from JSON Schema
- How to use the schema registry client from Lab 06 with Protobuf schemas

---

## Background: Protobuf vs JSON Schema

### Wire format

JSON Schema validates structure but the wire format is still plain JSON —
human-readable, self-describing, verbose. Protobuf serializes to a compact
binary format: field numbers instead of field names, variable-length integers,
no quotes or braces. A typical EPR event in JSON is ~300 bytes; the same event
in Protobuf binary is ~80–100 bytes.

---

### Schema as code

A JSON Schema is a document. A `.proto` file is a program — you compile it and
get generated classes in your target language. Your Go service gets a Go struct,
your Python service gets a Python class, your Java service gets a Java class,
and they all agree on field numbers and types because they were compiled from
the same source.

---

### Evolution rules

Protobuf has its own backward compatibility rules that are enforced at the
field-number level, not the field-name level:

| Change                                      | Backward compatible?                                      |
| ------------------------------------------- | --------------------------------------------------------- |
| Add a new optional field (new field number) | Yes                                                       |
| Remove a field                              | Yes, but **reserve** the field number                     |
| Rename a field                              | Yes (wire format uses numbers, not names)                 |
| Change a field's type                       | Only for compatible types (e.g. int32→int64)              |
| Add a required field                        | **No** — proto3 has no required fields, this is by design |
| Reuse a deleted field number                | **Never** — silent data corruption                        |

Note that proto3 deliberately removed `required` fields. Everything is optional.
This is not a limitation — it is the mechanism that makes Protobuf inherently
more evolution-friendly than proto2 or JSON Schema with `required` arrays.

---

## Part 1 — Setup

### 1.1 Install dependencies

```bash
pip install grpcio-tools protobuf requests kafka-python
```

Verify `protoc` is available:

```bash
protoc --version
# libprotoc 3.x.x
```

If `protoc` is not installed:

```bash
# Ubuntu/Debian
sudo apt install -y protobuf-compiler

# macOS
brew install protobuf
```

---

### 1.2 Create the project structure

```bash
mkdir -p proto generated schemas
```

---

### 1.3 Create the lab topic

```bash
rpk topic create epr.events.proto \
  --partitions 3 \
  --replicas 1
```

---

## Part 2 — Define EPR Events in Protobuf

### 2.1 Write the initial .proto file

Create `proto/epr_event.proto`:

```protobuf
syntax = "proto3";

package epr.v1;

option go_package = "github.com/xbcsmith/epr/proto/v1";

// EventType enumerates the valid event types in the EPR pipeline.
// Add new values at the end. Never reuse or remove existing values.
enum EventType {
  EVENT_TYPE_UNSPECIFIED      = 0;
  EVENT_TYPE_BUILD_FINISHED   = 1;
  EVENT_TYPE_TEST_PASSED      = 2;
  EVENT_TYPE_TEST_FAILED      = 3;
  EVENT_TYPE_DEPLOY_STARTED   = 4;
  EVENT_TYPE_DEPLOY_FINISHED  = 5;
  EVENT_TYPE_SBOM_CREATED     = 6;
}

// EventStatus captures the outcome of a pipeline activity.
enum EventStatus {
  EVENT_STATUS_UNSPECIFIED = 0;
  EVENT_STATUS_SUCCESS     = 1;
  EVENT_STATUS_FAILURE     = 2;
  EVENT_STATUS_PENDING     = 3;
}

// EPREvent is the core message type published to the epr.events.proto topic.
// Field numbers are permanent. Once assigned, they must not be reused.
message EPREvent {
  // Core identity fields — the provenance key.
  // Together these uniquely identify an artifact at a point in a pipeline.
  string id           = 1;  // UUID
  EventType type      = 2;
  string name         = 3;  // Component name (e.g. "service-a")
  string version      = 4;  // Semantic version
  string release      = 5;  // Release identifier (e.g. "20250901.1")
  string platform_id  = 6;  // Target platform (e.g. "linux/amd64")
  string package      = 7;  // Package format (e.g. "rpm", "deb", "oci")

  // Event context
  string artifact_sha = 8;  // sha256:<hex> digest of the artifact
  string repo         = 9;  // Source repository URL
  EventStatus status  = 10;

  // Field numbers 11-19 reserved for future core fields.
  // Do not use them for other purposes.

  // Extended fields (optional, added in v1)
  int64 build_duration_ms = 20;  // Wall-clock build time in milliseconds
  string pipeline_id      = 21;  // CI pipeline run identifier
}
```

> **Field number discipline:** Field numbers 1–15 use single-byte encoding on
> the wire (more efficient). Reserve them for the fields that will be present in
> every message. Fields 16–2047 use two-byte encoding. The gap at 11–19 is
> intentional — it gives you room to add core fields later without jumping into
> the less-efficient range.

---

### 2.2 Compile the .proto file

```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=generated \
  proto/epr_event.proto

# Verify the generated file
ls generated/
# epr_event_pb2.py
```

---

### 2.3 Verify the generated code

```python
# Quick sanity check — run this in a Python REPL
import sys
sys.path.insert(0, 'generated')
from epr_event_pb2 import EPREvent, EventType, EventStatus

event = EPREvent(
    id="550e8400-e29b-41d4-a716-446655440000",
    type=EventType.EVENT_TYPE_BUILD_FINISHED,
    name="service-a",
    version="1.2.3",
    release="20250901.1",
    platform_id="linux/amd64",
    package="rpm",
    artifact_sha="sha256:abc123def456",
    repo="github.com/acme/service-a",
    status=EventStatus.EVENT_STATUS_SUCCESS,
)

print(event)
serialized = event.SerializeToString()
print(f"Serialized size: {len(serialized)} bytes")

# Round-trip
recovered = EPREvent()
recovered.ParseFromString(serialized)
print(f"Round-trip name: {recovered.name}")
```

---

## Part 3 — Register the Protobuf Schema

Redpanda's Schema Registry accepts Protobuf schemas with `schemaType` set to
`PROTOBUF` and the schema body as the raw `.proto` file text.

### 3.1 Register via curl

```bash
PROTO_CONTENT=$(cat proto/epr_event.proto | jq -Rs .)

curl -s -X POST \
  http://localhost:8081/subjects/epr.events.proto-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"PROTOBUF\", \"schema\": $PROTO_CONTENT}" \
  | jq .
```

Expected: `{"id": 10}` (or whatever the next global ID is in your registry).

---

### 3.2 Extend the schema registry client for Protobuf

Add these methods to `schema_registry.py` from Lab 06:

```python
def register_protobuf(self, subject: str, proto_text: str) -> int:
    """Register a Protobuf schema (.proto file contents) under a subject."""
    payload = {
        "schemaType": "PROTOBUF",
        "schema": proto_text,
    }
    resp = requests.post(
        f"{self.url}/subjects/{subject}/versions",
        json=payload,
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
    )
    resp.raise_for_status()
    return resp.json()["id"]

def get_protobuf_schema(self, subject: str, version: str = "latest") -> tuple[int, str]:
    """Returns (schema_id, proto_text) for a subject version."""
    resp = requests.get(f"{self.url}/subjects/{subject}/versions/{version}")
    resp.raise_for_status()
    data = resp.json()
    return data["id"], data["schema"]
```

---

### 3.3 Register and inspect via Python

Create `register_proto_schema.py`:

```python
#!/usr/bin/env python3
from schema_registry import SchemaRegistryClient

SUBJECT   = "epr.events.proto-value"
PROTO_FILE = "proto/epr_event.proto"

registry = SchemaRegistryClient()

with open(PROTO_FILE) as f:
    proto_text = f.read()

schema_id = registry.register_protobuf(SUBJECT, proto_text)
print(f"Registered schema ID: {schema_id}")
print(f"Versions: {registry.list_versions(SUBJECT)}")

sid, proto = registry.get_protobuf_schema(SUBJECT)
print(f"\nRegistered schema (id={sid}):\n{proto[:200]}...")
```

```bash
python register_proto_schema.py
```

---

## Part 4 — Protobuf Producer

Create `producer_proto.py`:

```python
#!/usr/bin/env python3
"""
Lab 07 producer — serializes EPR events to Protobuf binary and publishes
to Redpanda. Schema ID is embedded in a message header for consumer
reference.
"""

import sys
import uuid
import time
sys.path.insert(0, 'generated')

from kafka import KafkaProducer
from epr_event_pb2 import EPREvent, EventType, EventStatus
from schema_registry import SchemaRegistryClient

BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events.proto"
SUBJECT   = "epr.events.proto-value"

registry = SchemaRegistryClient()


def get_schema_id() -> int:
    schema_id, _, _ = registry.get_latest(SUBJECT)
    return schema_id


def make_event(
    event_type: EventType,
    name: str,
    version: str,
    release: str = "20250901.1",
    platform_id: str = "linux/amd64",
    package: str = "rpm",
    artifact_sha: str = "sha256:abc123def456abc1",
    repo: str = None,
    status: EventStatus = EventStatus.EVENT_STATUS_SUCCESS,
    build_duration_ms: int = 0,
    pipeline_id: str = "",
) -> EPREvent:
    return EPREvent(
        id=str(uuid.uuid4()),
        type=event_type,
        name=name,
        version=version,
        release=release,
        platform_id=platform_id,
        package=package,
        artifact_sha=artifact_sha,
        repo=repo or f"github.com/acme/{name}",
        status=status,
        build_duration_ms=build_duration_ms,
        pipeline_id=pipeline_id,
    )


def main():
    schema_id = get_schema_id()
    print(f"Using schema ID: {schema_id}\n")

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: v.SerializeToString(),
    )

    events = [
        make_event(EventType.EVENT_TYPE_BUILD_FINISHED,  "service-a", "1.2.3",
                   build_duration_ms=38400, pipeline_id="gh-run-001"),
        make_event(EventType.EVENT_TYPE_TEST_PASSED,     "service-a", "1.2.3",
                   build_duration_ms=12000, pipeline_id="gh-run-001"),
        make_event(EventType.EVENT_TYPE_DEPLOY_STARTED,  "service-a", "1.2.3",
                   pipeline_id="gh-run-001"),
        make_event(EventType.EVENT_TYPE_DEPLOY_FINISHED, "service-a", "1.2.3",
                   pipeline_id="gh-run-001"),
        make_event(EventType.EVENT_TYPE_BUILD_FINISHED,  "service-b", "0.9.1",
                   package="oci", artifact_sha="sha256:deadbeef12345678",
                   build_duration_ms=61000, pipeline_id="gh-run-002"),
        make_event(EventType.EVENT_TYPE_SBOM_CREATED,    "service-b", "0.9.1",
                   pipeline_id="gh-run-002"),
    ]

    for event in events:
        serialized = event.SerializeToString()
        headers = [("schema.id", str(schema_id).encode())]

        future = producer.send(TOPIC, value=event, headers=headers)
        meta = future.get(timeout=5)
        print(
            f"  SENT → {meta.topic}:{meta.partition}@{meta.offset}  "
            f"{EventType.Name(event.type)}  "
            f"{event.name}@{event.version}  "
            f"({len(serialized)} bytes)"
        )
        time.sleep(0.05)

    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()
```

---

Run it and note the byte sizes next to each message — compare them mentally to
the JSON payloads from Lab 06.

```bash
python producer_proto.py
```

---

## Part 5 — Protobuf Consumer

Create `consumer_proto.py`:

```python
#!/usr/bin/env python3
"""
Lab 07 consumer — deserializes Protobuf EPR events from Redpanda.
"""

import sys
sys.path.insert(0, 'generated')

from kafka import KafkaConsumer
from google.protobuf.message import DecodeError
from epr_event_pb2 import EPREvent, EventType, EventStatus
from schema_registry import SchemaRegistryClient

BOOTSTRAP = "localhost:9092"
TOPIC     = "epr.events.proto"
GROUP     = "epr-proto-consumer-v1"
SUBJECT   = "epr.events.proto-value"

registry = SchemaRegistryClient()


def decode_headers(headers) -> dict:
    return {k: v.decode("utf-8", errors="replace") for k, v in headers}


def process_event(event: EPREvent) -> None:
    type_name   = EventType.Name(event.type)
    status_name = EventStatus.Name(event.status)
    print(
        f"    ✓  {type_name:<30} "
        f"{event.name}@{event.version}  "
        f"platform={event.platform_id}  "
        f"status={status_name}"
    )
    if event.pipeline_id:
        print(f"       pipeline={event.pipeline_id}  "
              f"duration={event.build_duration_ms}ms")


def main():
    consumer_schema_id, _, _ = registry.get_latest(SUBJECT)
    print(f"Consumer schema ID: {consumer_schema_id}\n")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=5000,
    )

    processed = errors = 0

    for record in consumer:
        headers = decode_headers(record.headers)
        producer_schema_id = headers.get("schema.id", "unknown")

        print(f"  MSG  partition={record.partition} offset={record.offset}  "
              f"producer_schema_id={producer_schema_id}")

        if producer_schema_id != "unknown" and int(producer_schema_id) != consumer_schema_id:
            print(f"    ⚠  Schema ID mismatch — attempting to deserialize anyway "
                  f"(Protobuf is usually tolerant of version differences).")

        try:
            event = EPREvent()
            event.ParseFromString(record.value)
            process_event(event)
            processed += 1
        except DecodeError as e:
            print(f"    ✗  Protobuf decode error: {e}")
            errors += 1

        consumer.commit()

    consumer.close()
    print(f"\nProcessed: {processed}  |  Errors: {errors}")


if __name__ == "__main__":
    main()
```

```bash
python consumer_proto.py
```

---

## Part 6 — Schema Evolution with Protobuf

### 6.1 Add a new message type and field

Create `proto/epr_event_v2.proto` — adds a `ScanResult` embedded message and a
new `EVENT_TYPE_SCAN_COMPLETED` enum value:

```protobuf
syntax = "proto3";

package epr.v2;

option go_package = "github.com/xbcsmith/epr/proto/v2";

enum EventType {
  EVENT_TYPE_UNSPECIFIED      = 0;
  EVENT_TYPE_BUILD_FINISHED   = 1;
  EVENT_TYPE_TEST_PASSED      = 2;
  EVENT_TYPE_TEST_FAILED      = 3;
  EVENT_TYPE_DEPLOY_STARTED   = 4;
  EVENT_TYPE_DEPLOY_FINISHED  = 5;
  EVENT_TYPE_SBOM_CREATED     = 6;
  EVENT_TYPE_SCAN_COMPLETED   = 7;  // New in v2 — safe to add at the end
}

enum EventStatus {
  EVENT_STATUS_UNSPECIFIED = 0;
  EVENT_STATUS_SUCCESS     = 1;
  EVENT_STATUS_FAILURE     = 2;
  EVENT_STATUS_PENDING     = 3;
}

message ScanResult {
  int32  critical_count  = 1;
  int32  high_count      = 2;
  int32  medium_count    = 3;
  string scanner         = 4;
  string scanner_version = 5;
}

message EPREvent {
  // Core identity — field numbers identical to v1, never changed
  string      id           = 1;
  EventType   type         = 2;
  string      name         = 3;
  string      version      = 4;
  string      release      = 5;
  string      platform_id  = 6;
  string      package      = 7;
  string      artifact_sha = 8;
  string      repo         = 9;
  EventStatus status       = 10;

  // Extended fields — field numbers identical to v1
  int64  build_duration_ms = 20;
  string pipeline_id       = 21;

  // New in v2 — new field number, never previously used
  ScanResult scan_result = 22;
}
```

---

Compile and register:

```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=generated \
  proto/epr_event_v2.proto

PROTO_V2=$(cat proto/epr_event_v2.proto | jq -Rs .)
curl -s -X POST \
  http://localhost:8081/subjects/epr.events.proto-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"PROTOBUF\", \"schema\": $PROTO_V2}" \
  | jq .
```

---

### 6.2 Cross-version compatibility test

Create `cross_version_test.py` to prove the core Protobuf property: v1 consumers
can read v2 messages (unknown fields silently ignored), and v2 consumers can
read v1 messages (absent fields zero-valued).

```python
#!/usr/bin/env python3
"""
Demonstrates Protobuf's binary-level forward and backward compatibility.
No schema registry involvement needed — this is a property of the wire format.
"""

import sys, uuid
sys.path.insert(0, 'generated')

from epr_event_pb2   import EPREvent as V1, EventType as ET1, EventStatus as ES1
from epr_event_v2_pb2 import EPREvent as V2, EventType as ET2, EventStatus as ES2, ScanResult


def v2_producer_v1_consumer():
    """v2 message → v1 consumer: unknown scan_result field silently ignored."""
    msg = V2(
        id=str(uuid.uuid4()),
        type=ET2.EVENT_TYPE_SCAN_COMPLETED,
        name="service-a", version="1.2.3", release="20250901.1",
        platform_id="linux/amd64", package="oci",
        artifact_sha="sha256:abc123def456abc1",
        repo="github.com/acme/service-a",
        status=ES2.EVENT_STATUS_SUCCESS,
        pipeline_id="gh-run-007",
        scan_result=ScanResult(critical_count=0, high_count=2, scanner="trivy"),
    )

    parsed = V1()
    parsed.ParseFromString(msg.SerializeToString())

    print("v2 → v1 (forward compat):")
    print(f"  name readable: {parsed.name} ✓")
    print(f"  scan_result (unknown to v1): silently ignored ✓")
    print(f"  pipeline_id: {parsed.pipeline_id} ✓\n")


def v1_producer_v2_consumer():
    """v1 message → v2 consumer: absent scan_result is zero-valued."""
    msg = V1(
        id=str(uuid.uuid4()),
        type=ET1.EVENT_TYPE_BUILD_FINISHED,
        name="legacy-service", version="0.1.0", release="20240101.1",
        platform_id="linux/amd64", package="rpm",
        artifact_sha="sha256:abc123def456abc1",
        repo="github.com/acme/legacy-service",
        status=ES1.EVENT_STATUS_SUCCESS,
    )

    parsed = V2()
    parsed.ParseFromString(msg.SerializeToString())

    print("v1 → v2 (backward compat):")
    print(f"  name readable: {parsed.name} ✓")
    print(f"  scan_result.critical_count: {parsed.scan_result.critical_count} (zero — absent in v1) ✓")
    print(f"  pipeline_id: '{parsed.pipeline_id}' (empty — absent in v1) ✓\n")


def field_rename_is_transparent():
    """Field names are not on the wire — renaming is invisible to consumers."""
    msg = V1(
        id=str(uuid.uuid4()), type=ET1.EVENT_TYPE_BUILD_FINISHED,
        name="service-x", version="3.0.0", release="20250901.1",
        platform_id="darwin/arm64", package="pkg",
        artifact_sha="sha256:abc123def456abc1",
        repo="github.com/acme/service-x",
        status=ES1.EVENT_STATUS_SUCCESS,
    )

    parsed = V2()
    parsed.ParseFromString(msg.SerializeToString())

    print("Field rename transparency:")
    print(f"  v1 platform_id (field 6): '{msg.platform_id}'")
    print(f"  v2 platform_id (field 6): '{parsed.platform_id}' ✓")
    print(f"  Wire uses field numbers — renaming a field is a no-op for consumers.\n")


if __name__ == "__main__":
    v2_producer_v1_consumer()
    v1_producer_v2_consumer()
    field_rename_is_transparent()
```

```bash
python cross_version_test.py
```

---

### 6.3 The one rule you must never break: field number reuse

Run this in a Python REPL to see what happens when you try to parse string bytes
as an integer — the result of silently reusing a field number with a different
type:

```python
import sys
sys.path.insert(0, 'generated')
from epr_event_pb2 import EPREvent, EventType, EventStatus
import uuid

# Field 7 is 'package' (string). If someone deleted it and reused
# field 7 for an int32, any consumer still using the old schema
# would try to interpret string bytes as an integer.
event = EPREvent(
    id=str(uuid.uuid4()), type=EventType.EVENT_TYPE_BUILD_FINISHED,
    name="service-y", version="1.0.0", release="20250901.1",
    platform_id="linux/amd64", package="deb",
    artifact_sha="sha256:abc123def456abc1",
    repo="github.com/acme/service-y",
    status=EventStatus.EVENT_STATUS_SUCCESS,
)
wire = event.SerializeToString()
print(f"Field 7 ('package') on wire contains the bytes for string 'deb'.")
print(f"If a new int32 field reused number 7, parsing 'deb' as a varint")
print(f"would produce a wrong value or a DecodeError.")
print(f"\nCorrect deletion procedure:")
print(f"  reserved 7;")
print(f"  reserved \"package\";")
```

---

### 6.4 Size comparison

Create `size_comparison.py`:

```python
#!/usr/bin/env python3
"""Compare JSON vs Protobuf message sizes for a typical EPR event."""

import sys, json, uuid
sys.path.insert(0, 'generated')
from epr_event_pb2 import EPREvent, EventType, EventStatus

EVENT_ID = str(uuid.uuid4())

json_event = {
    "id": EVENT_ID,
    "type": "build.finished",
    "artifact_sha": "sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
    "repo": "github.com/acme/service-a",
    "status": "success",
    "name": "service-a",
    "version": "1.2.3",
    "release": "20250901.1",
    "platform_id": "linux/amd64",
    "package": "rpm",
    "build_duration_ms": 38400,
    "pipeline_id": "gh-actions-run-12345",
}

proto_event = EPREvent(
    id=EVENT_ID,
    type=EventType.EVENT_TYPE_BUILD_FINISHED,
    artifact_sha="sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
    repo="github.com/acme/service-a",
    status=EventStatus.EVENT_STATUS_SUCCESS,
    name="service-a",
    version="1.2.3",
    release="20250901.1",
    platform_id="linux/amd64",
    package="rpm",
    build_duration_ms=38400,
    pipeline_id="gh-actions-run-12345",
)

json_bytes  = json.dumps(json_event).encode("utf-8")
proto_bytes = proto_event.SerializeToString()

print(f"JSON:     {len(json_bytes):>4} bytes")
print(f"Protobuf: {len(proto_bytes):>4} bytes")
print(f"Ratio:    {len(json_bytes) / len(proto_bytes):.1f}x smaller with Protobuf")
```

```bash
python size_comparison.py
```

---

## Part 7 — Challenge Exercises

### Challenge A: Go code generation

Generate Go structs from the same `.proto` file and prove binary
interoperability between a Go producer and the Python consumer.

```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest

protoc \
  -I proto \
  --go_out=generated_go \
  proto/epr_event.proto
```

Write a Go program that produces a `EPREvent` to Redpanda and verify
`consumer_proto.py` reads it correctly without modification.

---

### Challenge B: Confluent wire format envelope

The Confluent wire format embeds the schema ID in the first 5 bytes of every
message value (`\x00` magic byte + 4-byte big-endian schema ID). Implement this
in both producer and consumer so the schema ID travels in the value rather than
a header.

```python
import struct

def encode_with_schema_id(schema_id: int, proto_bytes: bytes) -> bytes:
    return struct.pack(">bI", 0, schema_id) + proto_bytes

def decode_with_schema_id(data: bytes) -> tuple[int, bytes]:
    magic, schema_id = struct.unpack(">bI", data[:5])
    assert magic == 0
    return schema_id, data[5:]
```

---

### Challenge C: Protobuf + DLQ

Modify `consumer_proto.py` to route `DecodeError` failures to
`epr.events.proto.dlq`. Add a `dlq.schema.id` header from the message header.
Write a DLQ inspector that tries to deserialize DLQ messages with both v1 and v2
schemas, reporting which version (if either) can successfully parse the payload.

### Challenge D: Enum exhaustion and graceful handling

Add 10 new plausible CI/CD event types to `epr_event_v2.proto` (e.g.
`EVENT_TYPE_CONTAINER_PUSHED`, `EVENT_TYPE_POLICY_EVALUATED`). Register the new
schema. Write a consumer using Python 3.10+ `match`/`case` that handles each
known type explicitly and logs unknown enum values rather than crashing —
demonstrating graceful handling of values added by a newer producer schema.

---

## Cleanup

```bash
rpk topic delete epr.events.proto

curl -s -X DELETE http://localhost:8081/subjects/epr.events.proto-value | jq .
curl -s -X DELETE "http://localhost:8081/subjects/epr.events.proto-value?permanent=true" | jq .

rm -rf generated_go/
```

---

**Duration:** ~60 minutes **Prerequisites:** Lab 06 complete; `protoc`
installed; Python 3.10+ with `kafka-python`, `requests`, `grpcio-tools`, and
`protobuf` installed.

---

## Key Takeaways

- **Protobuf schema evolution is governed by field numbers**, not field names.
  Field numbers are permanent — add, never reassign.
- **proto3 has no required fields by design.** This makes every Protobuf schema
  inherently evolution-friendly. The tradeoff is that consumers must handle zero
  values for absent fields.
- **Renaming fields is free** — the wire format uses numbers, consumers never
  see field names.
- **`reserved` is the deletion mechanism.** Never delete a field without
  reserving its number and name. Silent data corruption from field number reuse
  is one of the hardest bugs to diagnose.
- **Binary size matters at scale.** For a CI/CD system generating thousands of
  build events per hour, Protobuf's 3–5x size reduction translates directly to
  broker storage and network throughput.
- **JSON Schema and Protobuf are not competitors** — they solve different
  problems. JSON Schema is great for validation-heavy workflows where human
  readability matters. Protobuf is great when you need generated, type-safe
  clients across multiple languages and care about wire efficiency.
- **The schema registry treats them the same way** — both get versioned, both
  get compatibility checks, both participate in the same subject/version/ID
  model.

---

## Further Reading

- [Redpanda Schema Registry Documentation](https://docs.redpanda.com/current/manage/schema-registry/)
- [Protocol Buffers Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/)
- [grpc_tools Python package](https://pypi.org/project/grpcio-tools/)
- [Protobuf Style Guide](https://protobuf.dev/programming-guides/style/)

---
