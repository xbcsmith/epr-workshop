# Agent Watcher: Generic

In this section, we will create a generic agent watcher that can monitor any
agent's state and log changes. This will allow us to keep track of multiple
agents without having to create specific watchers for each one.

---

## XZatoma install

First install rust:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then install xzatoma:

```bash
cargo install --git https://github.com/xbcsmith/xzatoma
```

---

## XZatoma generic watcher workshop

### Setup

Create a work directory

```bash
mkdir -p ./src/generic
cd ./src/generic
```

---

### Configuration

Create a config file.

```bash
touch config.yaml
```

```yaml
# XZatoma Generic Watcher Demo Configuration
#
# Standalone Kafka/Redpanda watcher that consumes plan JSON events from an
# input topic, executes them via the agent, and publishes result events to an
# output topic.
#
# Run from the ./src/generic/ directory:
#
#   cd ./src/generic
#   xzatoma watch -config config.yaml

provider:
  type: ollama
  ollama:
    host: http://localhost:11434
    # model: granite4:3b # alternative for smaller GPU
    # model: gemma4:e2b # good for testing, faster and cheaper than e4b but less capable
    model: gemma4:e4b-mlx # Mac specific model with optimizations for Apple Silicon, adjust if using a different platform

agent:
  max_turns: 20
  timeout_seconds: 600

  conversation:
    max_tokens: 32000
    min_retain_turns: 2
    prune_threshold: 0.80
    warning_threshold: 0.85
    auto_summary_threshold: 0.90

  tools:
    max_output_size: 262144
    max_file_read_size: 1048576

  terminal:
    default_mode: restricted_autonomous
    timeout_seconds: 30
    max_stdout_bytes: 262144
    max_stderr_bytes: 65536

watcher:
  watcher_type: generic

  kafka:
    # Redpanda external listener (mapped to localhost:19092 by docker-compose)
    brokers: "localhost:19092"

    # Input topic - plan events are consumed from here
    topic: "xzatoma.plans"

    # Output topic - PlanResultEvent messages are published here after each execution
    output_topic: "xzatoma.results"

    # Consumer group ID - change this to reset offsets and replay all events
    group_id: "xzatoma-generic-demo"

    # Create topics automatically at startup
    auto_create_topics: true
    num_partitions: 1
    replication_factor: 1

    # Redpanda in dev-container mode does not require TLS or SASL
    security:
      protocol: "PLAINTEXT"

  logging:
    level: "info"
    json_format: false
    include_payload: true

  execution:
    allow_dangerous: false
    max_concurrent_executions: 1
    execution_timeout_secs: 300
    execution_mode: per_task
```

---

### Seed Events

Create a seed event script to publish a plan event to the input topic.

```bash
touch seed_plan.py
```

```python
#!/usr/bin/env python3
"""Publish a Plan event to Kafka using kafka-python.

Usage:
  python3 seed_plan.py [PRESET]
  python3 seed_plan.py --stdin

Presets:
  hello   (default)  hello-world plan with action "greet"
  health             system-health plan with action "report"
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

try:
    from kafka import KafkaProducer, KafkaAdminClient
    from kafka.admin import NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError as exc:
    raise SystemExit(
        "kafka-python is required. Install it with: python3 -m pip install kafka-python"
    ) from exc




def die(message: str) -> None:
    print(f"[seed_plan] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def warn(message: str) -> None:
    print(f"[seed_plan] WARNING: {message}", file=sys.stderr)


def log(message: str) -> None:
    print(f"[seed_plan] {message}")


def gen_id() -> str:
    try:
        import ulid

        return str(ulid.new())
    except Exception:
        return f"task-{int(time.time())}-{random.randint(0, 999999):06d}"


def format_time() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_preset_plan(preset: str) -> dict:
    if preset == "hello":
        plan_id = gen_id()
        task_id = gen_id()
        return {
            "id": plan_id,
            "name": "hello-world",
            "description": "Simple greeting plan to verify the generic watcher is running.",
            "action": "greet",
            "version": "1.0.0",
            "goals": ["Confirm the generic watcher received and executed this plan"],
            "tasks": [
                {
                    "id": task_id,
                    "description": (
                        "You are XZatoma running in generic watcher mode. Run these three commands and report each one with its output: "
                        "(1) echo Generic watcher is alive (2) date -u (3) uname -s. Then run mkdir -p tmp and write a brief report to tmp/hello-world-report.txt containing: "
                        "a header line XZatoma Generic Watcher - Hello World, the timestamp from command 2, and the platform from command 3. Finish with cat tmp/hello-world-report.txt to confirm the file was written."
                    ),
                    "priority": "low",
                }
            ],
            "max_iterations": 5,
            "allow_dangerous": False,
            "result_mentions": ["tmp/hello-world-report.txt"],
        }

    if preset == "health":
        plan_id = gen_id()
        task_id_1 = gen_id()
        task_id_2 = gen_id()
        return {
            "id": plan_id,
            "name": "system-health",
            "description": "Basic system health check - runs diagnostics and writes a report file.",
            "action": "report",
            "version": "1.0.0",
            "goals": ["Collect and report current system health metrics"],
            "tasks": [
                {
                    "id": task_id_1,
                    "description": (
                        "Gather system information by running each of the following commands and reporting the command name and its output clearly: uname -a, date -u, df -h ."
                    ),
                    "priority": "high",
                },
                {
                    "id": task_id_2,
                    "description": (
                        "Write a plain-text system health report to ./tmp/system-health-report.txt. First run mkdir -p ./tmp to ensure the directory exists. "
                        "The report must contain: a header line System Health Report, a timestamp from date -u, the platform info from uname -a, a disk usage section from df -h ., and a footer line end of report. "
                        "After writing confirm the file exists with head -3 tmp/system-health-report.txt."
                    ),
                    "priority": "medium",
                },
            ],
            "max_iterations": 8,
            "allow_dangerous": False,
            "result_mentions": ["tmp/system-health-report.txt"],
        }



    die(f"Unknown preset '{preset}'. Valid presets: hello, health")


def build_envelope(plan: dict) -> dict:
    return {
        "id": gen_id(),
        "specversion": "1.0",
        "type": "xzatoma.plan.execute",
        "source": "xzatoma.seed-plan",
        "time": format_time(),
        "datacontenttype": "application/json",
        "data": plan,
    }


def ensure_topic(admin_client: KafkaAdminClient, topic: str) -> None:
    try:
        admin_client.create_topics([NewTopic(name=topic, num_partitions=1, replication_factor=1)])
        log(f"Ensured topic '{topic}' exists.")
    except TopicAlreadyExistsError:
        log(f"Topic '{topic}' already exists.")
    except Exception as exc:
        warn(f"Could not create topic '{topic}': {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a Plan event to Kafka using kafka-python.")
    parser.add_argument("preset", nargs="?", default="hello", choices=["hello", "health"], help="Preset plan to send")
    parser.add_argument("--stdin", action="store_true", help="Read a custom plan JSON document from stdin")
    parser.add_argument("--topic", default=os.environ.get("XZATOMA_TOPIC", "xzatoma.plans"), help="Kafka topic to publish to")
    parser.add_argument("--brokers", default=os.environ.get("XZATOMA_BROKERS", "localhost:9092"), help="Kafka bootstrap brokers")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.stdin and args.preset != "hello":
        log("Ignoring positional preset when --stdin is used.")

    if args.stdin:
        raw = sys.stdin.read()
        if not raw.strip():
            die("No input received on stdin. Pipe a Plan JSON document to this script.")
        try:
            plan = json.loads(raw)
        except json.JSONDecodeError as exc:
            die(f"Plan payload is not valid JSON: {exc}")
        plan_name = plan.get("name", "(unknown)")
        plan_action = plan.get("action", "(none)")
        plan_version = plan.get("version", "(none)")
        plan_id = plan.get("id", "(none)")
    else:
        plan = load_preset_plan(args.preset)
        plan_name = plan["name"]
        plan_action = plan["action"]
        plan_version = plan.get("version", "(none)")
        plan_id = plan.get("id", "(none)")

    envelope = build_envelope(plan)
    brokers = [broker.strip() for broker in args.brokers.split(",") if broker.strip()]

    try:
        admin_client = KafkaAdminClient(bootstrap_servers=brokers)
        ensure_topic(admin_client, args.topic)
        admin_client.close()
    except Exception as exc:
        warn(f"Kafka admin client failed: {exc}")

    try:
        producer = KafkaProducer(
            bootstrap_servers=brokers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        metadata = producer.send(args.topic, envelope).get(timeout=10)
        producer.flush()
        producer.close()
    except Exception as exc:
        die(f"Failed to publish plan event: {exc}")

    log(f"Publishing plan event to topic '{args.topic}' ...")
    log(f"  ID      : {plan_id}")
    log(f"  Name    : {plan_name}")
    log(f"  Action  : {plan_action}")
    log(f"  Version : {plan_version}")
    log(f"  Partition: {metadata.partition}, Offset: {metadata.offset}")

    print("\nPayload published:")
    print(json.dumps(envelope, indent=2))

    print("\nNext steps:")
    print("  1. Start XZatoma in generic watcher mode if it is not running.")
    print("  2. XZatoma should pick up the plan event and publish a PlanResultEvent to the output topic.")
    print("  3. Watch the result in a separate terminal or via your Kafka monitoring tools.")
    print("  4. To send another event with a different preset:")
    print("       python3 seed_plan.py hello")
    print("       python3 seed_plan.py health")
    print("  5. To send a custom plan via stdin:")
    print("       echo '{\"name\":\"my-plan\",\"action\":\"deploy\",\"version\":\"2.0.0\",\"tasks\":[{\"id\":\"deploy-task\",\"description\":\"Run: echo deployed\"}]}' | python3 seed_plan.py --stdin")


if __name__ == "__main__":
    main()
```

---

## Run the Demo

In terminal one start xzatoma in watcher mode:

```bash
xzatoma watch --config config.yaml
```

In terminal two run the Redpanda console consumer to monitor the output topic
for results:

```bash
docker exec redpanda-0 \
        rpk topic consume "xzatoma.results" \
        --brokers "localhost:9092"
```

In terminal three run the seed script to create receivers and events:

```bash
python3 seed_plan.py
```

---

## Conclusion

This generic watcher setup allows you to easily monitor and execute plans from
any source that can publish to Kafka. You can extend this by creating more
complex plans, integrating with other tools, or building dashboards to visualize
the results. The flexibility of the generic watcher means you can adapt it to a
wide variety of use cases without needing to change the core logic of your
agents.
