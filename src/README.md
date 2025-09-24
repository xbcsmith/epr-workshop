# EPR Workshop Source Code

## Install Requirements

```bash
python3 -m venv ./venv/epr
source ./venv/epr/bin/activate
pip install -r requirements.txt
```

## Generate CDEvents

The `generate_cdevents.py` script is a Python utility for generating and handling CDEvents (Continuous Delivery Events) based on the CDEvents specification. It creates synthetic events for various CI/CD activities, such as pipeline runs, artifact packaging, builds, tests, and deployments, across multiple simulated services (e.g., "foo", "bar").

Key Functionality

Event Generation: The generate_events() function produces a list of CDEvents, each with unique IDs (using ULID), timestamps, and structured data tailored to the event type. It iterates over predefined service names and event types, populating fields like context (metadata) and subject (event-specific details) to match CDEvents schemas.

Posting Events: Post CDEvents to CDViz. The post_event() and post_events() use the httpx library to send individual or multiple events as JSON payloads to a specified webhook URL (default: http://localhost:8080/webhook/000-cdevents).

Dry-Run and Output Options: The script supports command-line arguments to either post events directly, print equivalent curl commands for manual execution, or write events to disk as JSON files.

Usage

Run the script with options like --dry-run to preview commands or --write-to-disk to save events locally. It integrates with EPR (Event Provenance Registry) workflows by generating events that can be ingested via webhooks for testing or demonstration purposes.

## Consumer

The `consumer.py` script is a Kafka consumer that reads messages from a specified Kafka topic, typically for processing EPR (Event Provenance Registry) events.

Key Functionality

Configuration: It retrieves Kafka broker addresses and topic name from environment variables (EPR_BROKERS and EPR_TOPIC), defaulting to localhost:9092 and epr.dev.events if not set.

Consumer Setup: Creates a KafkaConsumer instance with settings for group ID (epr-python-consumer), starting from the earliest available offset, disabling auto-commit, and a 1-second timeout for polling.

Message Consumption: Subscribes to the topic and iterates over incoming messages, printing each message's partition, offset, key, and value to stdout for logging or debugging.

Error Handling: Catches and prints any exceptions during consumption, then closes the consumer connection.

This is useful for monitoring or processing event streams in a Kafka-based EPR system. For full details, see the script in `consumer.py`.