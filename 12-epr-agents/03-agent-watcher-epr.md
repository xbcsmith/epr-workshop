# Agent Watcher: EPR-Specific

In this section, we will create an agent watcher that is specifically designed
to monitor agents registered in the Event Provenance Registry (EPR). This
watcher will be able to track the state of agents, log changes, and provide
insights into their activity within the EPR ecosystem.

---

## EPR Agent Watcher

This session shows XZatoma running in **XZepr watcher mode**: a long-running
process that consumes EPR Events from a Redpanda topic, extracts the embedded
plan from each event payload, executes it autonomously through the configured AI
provider, and publishes a result event back to an output topic.

XZatoma's XZepr watcher bridges the EPR event bus with autonomous AI-driven plan
execution: when a qualifying build, deployment, or pipeline event arrives,
XZatoma automatically runs the plan embedded in that event and reports the
outcome.

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

## XZatoma EPR watcher workshop

### Setup

Create a work directory

```bash
mkdir -p ./src/epr
cd ./src/epr
```

---

### Configuration

Create a config file.

```bash
touch config.yaml
```

```yaml
# XZatoma EPR Watcher Demo Configuration
#
# Consumes EPR Events from Redpanda and executes the plans embedded
# in each event payload via the AI agent.
#
# Run from the ./src/epr/ directory:
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
  watcher_type: xzepr

  kafka:
    # Redpanda external listener (mapped to localhost:19092 by docker-compose)
    brokers: "localhost:19092"

    # Input topic - XZepr CloudEvents are consumed from here
    # topic: "xzepr.events"
    topic: "epr.dev.events"

    # Output topic - result events are published here after each execution
    output_topic: "xzepr.results"

    # Consumer group ID
    group_id: "xzatoma-xzepr-demo"

    # Create topics automatically at startup
    auto_create_topics: true
    num_partitions: 1
    replication_factor: 1

    # Redpanda in dev-container mode does not require TLS or SASL
    security:
      protocol: "PLAINTEXT"

  filters:
    event_types:
      - "xzepr.build.receiver"
      - "xzepr.deploy.receiver"
    success_only: true

  logging:
    level: "info"
    json_format: false
    include_payload: true

  execution:
    allow_dangerous: true
    max_concurrent_executions: 1
    execution_timeout_secs: 300
```

---

### Seeding the EPR

Create the `seed_epr.py` script to populate the EPR with sample receivers and
events for testing.

```bash
touch seed_epr.py
```

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#

import sys

import httpx

receiver_url = "http://localhost:8042/api/v1/receivers"
events_url = "http://localhost:8042/api/v1/events"

def _post(url, data):
    try:
        response = httpx.post(url, json=data)
        response.raise_for_status()
        print(f"Successfully posted to {url}: {response.status_code}")
        return response.json()
    except httpx.HTTPError as e:
        print(f"HTTP error occurred while posting to {url}: {e}")
    except Exception as e:
        print(f"An error occurred while posting to {url}: {e}")


def create_build_receiver():
    print("Creating build receiver...")
    build_receiver = {
          "name": "build_receiver",
          "type": "xzepr.build.receiver",
          "version": "1.0.0",
          "description": "Build event receiver for XZepr watcher demo.",
          "schema": {}
    }
    return _post(receiver_url, build_receiver)

def create_build_receiver_event(build_receiver_id):
    build_event = {
    "name": "build-verify",
    "version": "1.0.0",
    "release": "1.0.0",
    "platform_id": "local",
    "package": "xzatoma-demo",
    "description": "Verify build artifacts after a successful build",
    "payload": {
        "plan": "{\"id\":\"01JXZEPR0BUILD0PLAN000001\",\"name\":\"build-verify\",\"description\":\"Verify XZatoma build artifacts after a successful build.success event from XZepr.\",\"action\":\"verify\",\"version\":\"1.0.0\",\"goals\":[\"Confirm the XZepr watcher received and executed this build event\",\"Write a build verification report to tmp/\"],\"tasks\":[{\"id\":\"01JXZEPR0BUILD0TASK000001\",\"description\":\"Run the following commands and report each one with its output: (1) echo XZatoma XZepr watcher received build.success event (2) date -u (3) uname -s. Format each result as COMMAND: <command> OUTPUT: <output>. If any command fails report the error and continue.\",\"priority\":\"high\",\"dependencies\":[]},{\"id\":\"01JXZEPR0BUILD0TASK000002\",\"description\":\"Write a brief build verification report to tmp/build-verify-report.txt. First run mkdir -p tmp to ensure the directory exists. The report must contain: a header line XZatoma Build Verification Report, the timestamp from the previous task, the platform name from the previous task, and a footer line end of report. After writing confirm the file with cat tmp/build-verify-report.txt.\",\"priority\":\"medium\",\"dependencies\":[\"01JXZEPR0BUILD0TASK000001\"]}],\"max_iterations\":5,\"allow_dangerous\":false,\"result_mentions\":[\"tmp/build-verify-report.txt\"]}"
    },
    "success": True,
    "event_receiver_id": build_receiver_id,
    }
    return _post(events_url, build_event)

def create_deploy_receiver():
    print("Creating deploy receiver...")
    deploy_receiver = {
          "name": "deploy_receiver",
          "type": "xzepr.deploy.receiver",
          "version": "1.0.0",
          "description": "Deploy event receiver for XZepr watcher demo.",
          "schema": {}
    }
    return _post(receiver_url, deploy_receiver)

def create_deploy_receiver_event(deploy_receiver_id):
    deploy_event = {
      "name": "deploy-verify",
      "version": "1.0.0",
      "release": "1.0.0",
      "platform_id": "local",
      "package": "xzatoma-demo",
      "description": "Verify deployment health after a successful deployment event",
      "payload": {
        "plan": "{\"id\":\"01JXZEPR0DEPLOY0PLAN00001\",\"name\":\"deploy-verify\",\"description\":\"Verify XZatoma deployment health after a successful deployment event.\",\"action\":\"verify\",\"version\":\"1.0.0\",\"goals\":[\"Confirm the XZepr watcher received and executed this deployment event\"],\"tasks\":[{\"id\":\"01JXZEPR0DEPLOY0TASK00001\",\"description\":\"Gather deployment environment information by running the following commands and reporting each one with its output: (1) echo XZatoma XZepr watcher received deployment.success event (2) date -u (3) uname -a (4) df -h . Format each result as COMMAND: <command> OUTPUT: <output>.\",\"priority\":\"high\"},{\"id\":\"01JXZEPR0DEPLOY0TASK00002\",\"description\":\"Write a deployment health report to tmp/deploy-verify-report.txt. First run mkdir -p tmp to ensure the directory exists. The report must contain: a header line XZatoma Deployment Verification Report, the event type deployment.success, the timestamp from the previous task, the platform info from the previous task, a disk usage section from the previous task, and a footer line end of report. After writing confirm the file with cat tmp/deploy-verify-report.txt.\",\"priority\":\"medium\",\"dependencies\":[\"01JXZEPR0DEPLOY0TASK00001\"]}],\"max_iterations\":8,\"allow_dangerous\":false,\"result_mentions\":[\"tmp/deploy-verify-report.txt\"]}"
      },
      "success": True,
      "event_receiver_id": "${DEPLOY_RECEIVER}"
    }
    return _post(events_url, deploy_event)

def main(args):
    if "build" in args:
        build_receiver_response = create_build_receiver()
        if build_receiver_response and "data" in build_receiver_response:
            build_receiver_id = build_receiver_response["data"]
            print(f"Build receiver created with ID: {build_receiver_id}")
            build_event_response = create_build_receiver_event(build_receiver_id)
            print(f"Build event response: {build_event_response}")
        else:
            print("Failed to create build receiver. No ID returned.")
    elif "deploy" in args:
        deploy_receiver_response = create_deploy_receiver()
        if deploy_receiver_response and "data" in deploy_receiver_response:
            deploy_receiver_id = deploy_receiver_response["data"]
            print(f"Deploy receiver created with ID: {deploy_receiver_id}")
            deploy_event_response = create_deploy_receiver_event(deploy_receiver_id)
            print(f"Deploy event response: {deploy_event_response}")
        else:
            print("Failed to create deploy receiver. No ID returned.")
    else:
        print("No valid preset specified. Use 'build' or 'deploy' as an argument.")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

---

### Run the Demo

In terminal one start xzatoma in watcher mode:

```bash
xzatoma watch --config config.yaml
```

In terminal two run the Redpanda console consumer to monitor the output topic
for results:

```bash
docker exec redpanda-0 \
        rpk topic consume "xzepr.results" \
        --brokers "localhost:9092"
```

In terminal three run the seed script to create receivers and events:

```bash
python seed_epr.py
```

---

## Conclusion

In this section, we built an EPR-specific agent watcher using XZatoma that
listens for build and deployment events, executes embedded plans autonomously,
and reports results back to the EPR ecosystem. This demonstrates how
event-driven agents can be integrated with EPR to automate responses to critical
events in the software lifecycle.
