# EPR Workshop Source Code

## Install Requirements

```bash
python3 -m venv ./venv/epr
source ./venv/epr/bin/activate
pip install -r requirements.txt
```

## Documentation

| Name                                        | Description                                             |
| ------------------------------------------- | ------------------------------------------------------- |
| [Cdevents Pipeline](./cdevents_pipeline.py) | Description for [CDEvents Pipeline](#cdevents-pipeline) |
| [Consumer](./consumer.py)                   | Description for [Consumer](#consumer)                   |
| [Generate Cdevents](./generate_cdevents.py) | Description for [Generate CDEvents](#generate-cdevents) |
| [Mini Broker](./mini_broker.py)             | Description for [Mini Broker](#mini-broker)             |


## Descriptions

### Generate CDEvents

The `generate_cdevents.py` script is a Python utility for generating and handling CDEvents (Continuous Delivery Events) based on the CDEvents specification. It creates synthetic events for various CI/CD activities, such as pipeline runs, artifact packaging, builds, tests, and deployments, across multiple simulated services (e.g., "foo", "bar").

Key Functionality

Event Generation: The `generate_events()` function produces a list of CDEvents, each with unique IDs (using ULID), timestamps, and structured data tailored to the event type. It iterates over predefined service names and event types, populating fields like context (metadata) and subject (event-specific details) to match CDEvents schemas.

Posting Events: Post CDEvents to CDViz. The `post_event()` and `post_events()` use the httpx library to send individual or multiple events as JSON payloads to a specified webhook URL (default: <http://localhost:8080/webhook/000-cdevents>).

Dry-Run and Output Options: The script supports command-line arguments to either post events directly, print equivalent curl commands for manual execution, or write events to disk as JSON files.

Usage

Run the script with options like `--dry-run` to preview commands or `--write-to-disk` to save events locally. It integrates with EPR (Event Provenance Registry) workflows by generating events that can be ingested via webhooks for testing or demonstration purposes.

### Consumer

The `consumer.py` script is a Kafka consumer that reads messages from a specified Kafka topic, typically for processing EPR (Event Provenance Registry) events.

Key Functionality

Configuration: It retrieves Kafka broker addresses and topic name from environment variables (EPR_BROKERS and EPR_TOPIC), defaulting to localhost:9092 and epr.dev.events if not set.

Consumer Setup: Creates a KafkaConsumer instance with settings for group ID (epr-python-consumer), starting from the earliest available offset, disabling auto-commit, and a 1-second timeout for polling.

Message Consumption: Subscribes to the topic and iterates over incoming messages, printing each message's partition, offset, key, and value to stdout for logging or debugging.

Error Handling: Catches and prints any exceptions during consumption, then closes the consumer connection.

This is useful for monitoring or processing event streams in a Kafka-based EPR system. For full details, see the script in `consumer.py`.

### Mini Broker

The `mini_broker.py` script implements a simple in-memory publish-subscribe (pub/sub) broker for handling events asynchronously in Python. It mimics the event-driven architecture described in the README.md, where scripts like `generate_cdevents.py` generate and post CDEvents (e.g., for CI/CD activities like artifact packaging or deployments), and `consumer.py` consumes events from a Kafka topic in an EPR (Event Provenance Registry) system.

Key Functionality

InMemoryBroker Class: Acts as a lightweight event broker without external dependencies like Kafka. It maintains a dictionary of subscribers (self.subscribers), where keys are event types (e.g., "dev.cdevents.artifact.packaged.0.2.0") and values are lists of callback functions.

publish(event): Asynchronously notifies all subscribers matching the event's type (or a wildcard "*"). It prints the event type and subject for logging, similar to how consumer.py prints message details from Kafka.
subscribe(event_type, callback): Registers a callback for a specific event type, allowing dynamic subscription.
Example Usage in main():

Creates a broker instance and subscribes a printer callback to all events ("*").

Generates a sample CDEvent (e.g., an artifact packaged event with fields like id, source, type, subject, time, and data), mirroring the synthetic events produced by `generate_cdevents.py`.

Publishes the event, triggering the callback to print details (type, subject, time, and data keys), akin to how consumer.py processes and logs incoming Kafka messages.

This script serves as a minimal, self-contained alternative to Kafka for testing or demonstrating event flows in EPR workflows, without needing a full Kafka setup. It highlights asynchronous event handling using asyncio, which could integrate with webhook posting in `generate_cdevents.py` for local development. For production, tools like Kafka (as in consumer.py) provide persistence and scalability.

### CDEvents Pipeline

The `cdevents_pipeline.py` script simulates a complete CI/CD pipeline using CDEvents (Continuous Delivery Events) and an in-memory event broker, building on the event-driven architecture described in the README.md. It extends the concepts from `generate_cdevents.py` (which generates synthetic CDEvents for CI/CD activities) and `mini_broker.py` (a simple in-memory pub/sub broker) by orchestrating a multi-stage pipeline where services react to events asynchronously, similar to how consumer.py processes Kafka events in an EPR (Event Provenance Registry) system.

Key Components and Functionality

CDEvent Classes: Defines CDEventContext, CDEventSubject, and CDEvent dataclasses to structure events following the CDEvents specification, including fields like id, type, timestamp, and chainId for traceability. These mirror the synthetic events generated in `generate_cdevents.py`.

EventBroker Interface and InMemoryEventBroker: Implements an abstract EventBroker with publish and subscribe methods. The InMemoryEventBroker class maintains a dictionary of subscribers and an event history list, publishing events asynchronously to callbacks (e.g., for specific event types or wildcards like "*"), akin to the pub/sub mechanism in mini_broker.py.

Service Classes: Simulate microservices in a CI/CD pipeline, each subscribing to relevant CDEvents and publishing new ones upon completion:

RepositoryService: Simulates a code push, publishing a repository.modified event.

BuildService: Subscribes to repository.modified, performs a simulated build, and publishes a build.finished event with an artifact ID.

SecurityScanService: Subscribes to build.finished, runs a simulated security scan, and publishes a testsuiterun.finished event.

DeploymentService: Subscribes to testsuiterun.finished (if passed), deploys the artifact, and publishes a service.deployed event.

PipelineOrchestrator: Coordinates the services, initializes subscriptions, monitors all events via a wildcard subscription, and runs the pipeline simulation. It starts with a simulated code push and waits for the chain of events to complete, logging and printing the event history.