# CloudEvents and EPR

In this session we will learn how we can use CloudEvents with the Event Provenance
Registry (EPR).

This workshop session that walks the user through creating CloudEvents JSON and posting them to the Event Provenance Registry (EPR) first with curl (REST API), then with the epr-cli. The workshop uses the EPR REST endpoints shown in the repo (localhost:8042). The CloudEvent JSON will be placed inside the EPR event payload field (so EPR stores the CloudEvent as the event payload).

## Prerequisites

EPR server running on `http://localhost:8042` (Quickstart completed).
curl, jq, and cat available in your shell.

For CLI section: Go toolchain and ability to build/install epr-cli as shown in the repo.
Workshop flow

Create an event receiver (classification) using curl.

Create a CloudEvent JSON file locally.

Post an event to EPR using curl, embedding the CloudEvent JSON in the payload.

Query the created event via REST to verify.

Install or build epr-cli.

Repeat the same flow using epr-cli (create receiver, then create event using the file content).

## Using curl (step-by-step)

Create an event receiver (with schema)

This receiver defines the schema that event payload should match (EPR expects an event receiver ID when creating events).

```bash
curl --location --request POST 'http://localhost:8042/api/v1/receivers' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "name": "cloudevents-receiver",
    "type": "com.example.cloudevents",
    "version": "1.0.0",
    "description": "Receiver for CloudEvents JSON payloads",
    "schema": {
      "type": "object",
      "properties": {
        "specversion": { "type": "string" },
        "id": { "type": "string" },
        "source": { "type": "string" },
        "type": { "type": "string" },
        "time": { "type": "string" },
        "datacontenttype": { "type": "string" },
        "data": {}
      },
      "required": ["specversion","id","source","type","data"]
    }
  }'
```

The server returns a JSON object with the data field containing the event receiver ULID. 

Capture it:

```bash
# Example: capture the returned receiver id into a shell variable (uses jq)
RESPONSE=$(curl -s --location --request POST 'http://localhost:8042/api/v1/receivers' \
  --header 'Content-Type: application/json' \
  --data-raw '{"name":"tmp","type":"tmp","version":"1.0","description":"tmp","schema":{}}')
RECEIVER_ID=$(echo "$RESPONSE" | jq -r .data)
echo "Receiver ID: $RECEIVER_ID"
```

Create a CloudEvent JSON file locally

Create a file called cloud_event.json containing a structured CloudEvent. This will be placed into the EPR event payload.

```json
{
  "specversion": "1.0",
  "id": "evt-12345-abc",
  "source": "urn:example:myservice",
  "type": "com.example.myservice.event.created",
  "time": "2025-09-21T12:00:00Z",
  "datacontenttype": "application/json",
  "subject": "order/1234",
  "data": {
    "orderId": 1234,
    "status": "created",
    "customer": {
      "id": "c-987",
      "email": "alice@example.com"
    }
  }
}
```

Save that JSON into the workshop directory as `cloud_event.json`.

Post an event to EPR (embedding the CloudEvent JSON in payload)

Use the event create REST endpoint. Set the event_receiver_id to the ID you captured. The payload field must contain the CloudEvent object (as JSON). Here we use command 

substitution to insert the file contents.

```bash
# Replace <RECEIVER_ID> with the value returned when you created the receiver.
RECEIVER_ID="<RECEIVER_ID>"

curl --location --request POST 'http://localhost:8042/api/v1/events' \
  --header 'Content-Type: application/json' \
  --data-raw "{
    \"name\": \"order-created\",
    \"version\": \"1.0.0\",
    \"release\": \"2025.09\",
    \"platform_id\": \"linux-x86_64\",
    \"package\": \"example-app\",
    \"description\": \"Order created event containing a CloudEvent as payload\",
    \"payload\": $(cat cloud_event.json),
    \"success\": true,
    \"event_receiver_id\": \"${RECEIVER_ID}\"
  }"
```

Successful response returns the event ULID in .data:

```json
{ "data": "01HXXXXXXXEXAMPLEEVENTID" }
```

Verify the created event via REST GET

Use the event id returned to fetch and inspect:

```bash
EVENT_ID="01HXXXXXXXEXAMPLEEVENTID"
curl --header 'Content-Type: application/json' \
  --location --request GET "http://localhost:8042/api/v1/events/${EVENT_ID}" | jq .
```

You should see your top-level event fields and the payload containing the CloudEvent JSON you posted.


### Using the EPR CLI (step-by-step)

Install / build the epr-cli

Build and install into your Go path (example from the repo). Adjust PREFIX as desired.

From the project root:

```bash
make PREFIX=$(go env GOPATH) install
```

If on macOS M1:

```bash
make PREFIX=$(go env GOPATH) install-darwin-arm64
```

Create an event receiver with epr-cli

Use epr-cli receiver create to create the same receiver. You can pass the schema inline or keep it minimal with {} for this demo.

```bash
# Dry-run to preview the receiver payload
epr-cli receiver create --name "cloudevents-cli" --version "1.0.0" \
  --description "CLI created CloudEvents receiver" --type "com.example.cloudevents" \
  --schema '{}' --dry-run
```

```bash
# Create the receiver for real (returns a ULID)
epr-cli receiver create --name "cloudevents-cli" --version "1.0.0" \
  --description "CLI created CloudEvents receiver" --type "com.example.cloudevents" \
  --schema '{}'
```

The successful command prints the ULID of the created receiver. Capture it for the event step.

Create an event with epr-cli using the cloud_event.json file

The CLI examples in the repo use --payload with an inline JSON string. To use a file, pass the file content via command substitution so the CLI receives a valid JSON string.

```bash
# Replace RECEIVER_ULID with the receiver id returned by the cli create command.
RECEIVER_ULID="01HYYYYYYYYRECEIVERID"

# Create event via CLI (dry-run first)
epr-cli event create --name "order-created" --version 1.0.0 --release "2025.09" \
  --platform-id "linux-x86_64" --package "example-app" --description "Order created with CloudEvent payload" \
  --success true --event-receiver-id "${RECEIVER_ULID}" --payload "$(cat cloud_event.json)" --dry-run

# Create the event for real (will return the event id)
epr-cli event create --name "order-created" --version 1.0.0 --release "2025.09" \
  --platform-id "linux-x86_64" --package "example-app" --description "Order created with CloudEvent payload" \
  --success true --event-receiver-id "${RECEIVER_ULID}" --payload "$(cat cloud_event.json)"
```

Capture the printed event ID and verify with epr-cli event search or the REST GET:

```bash
# Example using epr-cli search by id:
EVENT_ULID="01HXXXXXXXXXEVENTID"
epr-cli event search --id "${EVENT_ULID}" --fields all

# Or verify via REST:
curl --header 'Content-Type: application/json' \
  --location --request GET "http://localhost:8042/api/v1/events/${EVENT_ULID}" | jq .
```

### Notes, tips, and variations

- CloudEvent as payload: storing the structured CloudEvent inside the EPR event payload keeps the CloudEvent intact for later retrieval, replay, or auditing.
- Schema compatibility: ensure the EPR event receiver schema allows the CloudEvent JSON shape. If you create a strict schema, your payload must validate. Use `--dry-run` with epr-cli commands to preview payloads before creating resources.
- Multi-event workflows: create multiple receivers and post different CloudEvents to each to simulate pipelines; you can then create receiver groups (see earlier docs) to produce aggregated behavior.


If the CloudEvent file contains quotes/newlines that break shell interpolation, use --payload "$(jq -c . cloud_event.json)" to compactify the JSON before passing to the CLI.

Appendix — compact command examples for copy/paste

Create receiver via REST (single-line):

```bash
curl --location --request POST 'http://localhost:8042/api/v1/receivers' \
  --header 'Content-Type: application/json' \
  --data-raw '{"name":"cloudevents-receiver","type":"com.example.cloudevents","version":"1.0.0","description":"CE receiver","schema":{}}' | jq .
```

Create event via REST using file:

```bash
RECEIVER_ID="<RECEIVER_ID_HERE>"
curl --location --request POST 'http://localhost:8042/api/v1/events' \
  --header 'Content-Type: application/json' \
  --data-raw "{\"name\":\"order-created\",\"version\":\"1.0.0\",\"payload\":$(jq -c . cloud_event.json),\"success\":true,\"event_receiver_id\":\"${RECEIVER_ID}\"}" | jq .
```

### Wrap-up

You now know how to craft a structured CloudEvent JSON, embed it as the payload in an EPR event and create that event both via the REST API (curl) and via the epr-cli.
