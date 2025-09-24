## CDEvents

## Overview

CDEvents provides standardized event schemas for common CI/CD activities like builds, deployments, tests, and releases. Each event follows a CloudEvents specification format and includes contextual information about what happened, when, and where in your pipeline.

## Clone the specs

Clone the spec and checkout the latest stable version

```bash
mkdir ./src
cd ./src
git clone https://github.com/cdevents/spec
git checkout spec-v0.4
```

## Quick hands-on tasks

Before you dive into the larger example below, try these short exercises to build practical intuition for CDEvents and event-driven pipelines.

### Inspect a CDEvent JSON

Goal: Identify CloudEvents headers and key CDEvents fields.

Steps:
1. Save the "Example Build CDEvent" JSON (below in this document) to a file, for example `build-event.json`.
2. Use `jq` to inspect it:

```bash
# pretty-print the whole event
jq . build-event.json

# show a few important fields
jq '{id: .id, source: .source, type: .type, subject: .subject, time: .time}' build-event.json

# show CDEvents links inside data.context
jq '.data.context.links' build-event.json
```

Outcome: You can point out id, source, type, subject, and the links.pipelineRun that correlates this task to a pipeline.

### Filter events by type

Goal: Practice selecting only the events a consumer would care about from a stream of events.

Assume you have an [NDJSON](https://jsonlines.org) file with one JSON event per line, events.ndjson.

```bash
# Extract all artifact.packaged events (pattern match)
jq -c 'select(.type | test("artifact\\.packaged"))' events.ndjson

# Extract only taskRun finished events (exact match)
jq -c 'select(.type == "dev.cdevents.taskrun.finished.0.1.1")' events.ndjson

# Save filtered events to a file
jq -c 'select(.type == "dev.cdevents.taskrun.finished.0.1.1")' events.ndjson > taskrun-finished.ndjson
```

Outcome: You have patterns to implement event filters for consumers and alerts.

### Run a minimal in-memory publish/subscribe demo

Goal: See events flow through a simple broker and observe decoupling between publisher and consumer.

Save the snippet below as mini_broker.py and run python3 mini_broker.py.

```python
#!/usr/bin/env python3
# mini_broker.py
import asyncio
import uuid
from datetime import datetime

class InMemoryBroker:
    def __init__(self):
        self.subscribers = {}  # event_type -> [callbacks]

    async def publish(self, event: dict):
        print("PUBLISH:", event.get("type"), event.get("subject"))
        # notify matching subscribers and wildcard "*"
        for etype, callbacks in list(self.subscribers.items()):
            if etype == "*" or etype == event.get("type"):
                for cb in callbacks:
                    await cb(event)

    async def subscribe(self, event_type: str, callback):
        self.subscribers.setdefault(event_type, []).append(callback)

async def printer(event: dict):
    print("RECEIVED:", event.get("type"), event.get("subject"))
    print("  time:", event.get("time"))
    print("  data keys:", list(event.get("data", {}).keys()))
    print()

async def main():
    broker = InMemoryBroker()
    await broker.subscribe("*", printer)

    # example event (a minimal artifact.packaged)
    event = {
        "id": str(uuid.uuid4()),
        "source": "example.build",
        "type": "dev.cdevents.artifact.packaged.0.1.1",
        "subject": "registry.example.com/my-app:abc123",
        "time": datetime.utcnow().isoformat() + "Z",
        "data": {
            "artifact": {
                "id": "registry.example.com/my-app:abc123",
                "digest": "sha256:aaaaaaaa..."
            }
        }
    }

    await broker.publish(event)

if __name__ == "__main__":
    asyncio.run(main())
```

Outcome: Running this script prints the publish and receive logs, showing how a subscriber reacts without the publisher knowing subscribers exist.

### Correlate a taskRun to its pipelineRun

Goal: Practice following references between events to reconstruct a pipeline execution.

Steps:

From a taskRun event file (or NDJSON stream), extract the pipelineRun link:

```bash
# Extract pipelineRun link from a single event file
jq -r '.data.context.links.pipelineRun // empty' build-event.json
```

### Compare time fields to reconstruct ordering.

Outcome: You can trace how a task-level event maps back to its pipeline and reconstruct a simple timeline.

When you've finished these quick tasks, continue to the larger "CDEvents-based Event-Driven CI/CD Pipeline for OCI Containers" example below.

## CDEvents-based Event-Driven CI/CD Pipeline for OCI Containers


This example demonstrates a complete pipeline using CDEvents specification

```python
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import aiohttp
import logging
```

## Configure logging

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)
```

## CDEvents Core Classes

```python
@dataclass
    class CDEventContext:
    """CDEvents context following CloudEvents specification"""
    version: str = "0.4.0"
    id: str = None
    source: str = None
    type: str = None
    subject: str = None
    time: str = None


    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.time:
            self.time = datetime.utcnow().isoformat() + "Z"


@dataclass
class CDEventData:
    """Base CDEvent data structure"""
    pass

@dataclass
class RepositoryData(CDEventData):
    """Data for repository events"""
    repository: Dict[str, str]
    change: Dict[str, Any]

@dataclass
class BuildData(CDEventData):
    """Data for build events"""
    build: Dict[str, Any]
    artifact: Optional[Dict[str, Any]] = None

@dataclass
class TestData(CDEventData):
    """Data for test events"""
    test: Dict[str, Any]
    artifact: Dict[str, Any]

@dataclass
class DeploymentData(CDEventData):
    """Data for deployment events"""
    deployment: Dict[str, Any]
    artifact: Dict[str, Any]
    environment: Dict[str, str]

class CDEvent:
    """CDEvent wrapper following the specification"""


    def __init__(self, context: CDEventContext, data: CDEventData):
        self.context = context
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to CloudEvents format"""
        event_dict = asdict(self.context)
        event_dict["data"] = asdict(self.data)
        return event_dict

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
```

# Event Broker Interface

```python
class EventBroker(ABC):
    """Abstract event broker interface"""


    @abstractmethod
    async def publish(self, event: CDEvent):
        pass

    @abstractmethod
    async def subscribe(self, event_types: List[str], callback):
        pass


    class InMemoryEventBroker(EventBroker):
        """Simple in-memory event broker for demonstration"""


    def __init__(self):
        self.subscribers = {}
        self.events = []

    async def publish(self, event: CDEvent):
        """Publish event to all relevant subscribers"""
        logger.info(f"Publishing event: {event.context.type}")
        self.events.append(event)
        
        # Notify subscribers
        for event_type, callbacks in self.subscribers.items():
            if event.context.type == event_type or event_type == "*":
                for callback in callbacks:
                    await callback(event)

    async def subscribe(self, event_types: List[str], callback):
        """Subscribe to specific event types"""
        for event_type in event_types:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
```

# Pipeline Services

```python
class RepositoryService:
    """Simulates a Git repository service"""


    def __init__(self, broker: EventBroker):
        self.broker = broker

    async def simulate_code_push(self, repo_url: str, commit_sha: str):
        """Simulate a code push event"""
        context = CDEventContext(
            source="git.example.com/webhook",
            type="dev.cdevents.repository.modified.0.1.2",
            subject=repo_url
        )
        
        data = RepositoryData(
            repository={
                "id": repo_url,
                "name": "my-app",
                "url": repo_url
            },
            change={
                "id": commit_sha,
                "type": "push",
                "author": "developer@example.com"
            }
        )
        
        event = CDEvent(context, data)
        await self.broker.publish(event)
        logger.info(f"Code pushed to {repo_url}, commit: {commit_sha}")


class BuildService:
    """Container build service"""


    def __init__(self, broker: EventBroker):
        self.broker = broker
        # Subscribe to repository events
        asyncio.create_task(
            self.broker.subscribe(
                ["dev.cdevents.repository.modified.0.1.2"], 
                self.handle_repository_change
            )
        )

    async def handle_repository_change(self, event: CDEvent):
        """Handle repository change events"""
        repo_data = event.data
        await self.start_build(repo_data.repository["url"], repo_data.change["id"])

    async def start_build(self, repo_url: str, commit_sha: str):
        """Start container build process"""
        build_id = str(uuid.uuid4())
        
        # Emit build started event
        context = CDEventContext(
            source="build.example.com",
            type="dev.cdevents.taskrun.started.0.1.1",
            subject=f"build/{build_id}"
        )
        
        build_data = BuildData(
            build={
                "id": build_id,
                "source": repo_url,
                "commit": commit_sha,
                "status": "started"
            }
        )
        
        await self.broker.publish(CDEvent(context, build_data))
        
        # Simulate build process
        logger.info(f"Building container for commit {commit_sha}")
        await asyncio.sleep(2)  # Simulate build time
        
        # Build completed - emit artifact packaged event
        image_tag = f"my-app:{commit_sha[:8]}"
        image_digest = f"sha256:{'a' * 64}"  # Simulated digest
        
        context = CDEventContext(
            source="build.example.com",
            type="dev.cdevents.artifact.packaged.0.1.1",
            subject=f"registry.example.com/{image_tag}"
        )
        
        build_data = BuildData(
            build={
                "id": build_id,
                "status": "completed"
            },
            artifact={
                "id": f"registry.example.com/{image_tag}@{image_digest}",
                "type": "container",
                "digest": image_digest,
                "tags": [image_tag]
            }
        )
        
        await self.broker.publish(CDEvent(context, build_data))
        logger.info(f"Container built: {image_tag}")


class SecurityScanService:
    """Container security scanning service"""


    def __init__(self, broker: EventBroker):
        self.broker = broker
        # Subscribe to artifact packaged events
        asyncio.create_task(
            self.broker.subscribe(
                ["dev.cdevents.artifact.packaged.0.1.1"], 
                self.handle_artifact_packaged
            )
        )

    async def handle_artifact_packaged(self, event: CDEvent):
        """Handle new artifact events"""
        build_data = event.data
        if build_data.artifact:
            await self.scan_container(build_data.artifact)

    async def scan_container(self, artifact: Dict[str, Any]):
        """Perform security scan on container"""
        scan_id = str(uuid.uuid4())
        
        logger.info(f"Starting security scan for {artifact['id']}")
        
        # Simulate scanning
        await asyncio.sleep(1)
        
        # Emit test finished event
        context = CDEventContext(
            source="security-scanner.example.com",
            type="dev.cdevents.testcase.finished.0.1.1",
            subject=f"scan/{scan_id}"
        )
        
        test_data = TestData(
            test={
                "id": scan_id,
                "type": "security-scan",
                "outcome": "pass",  # or "fail"
                "reason": "No critical vulnerabilities found"
            },
            artifact=artifact
        )
        
        await self.broker.publish(CDEvent(context, test_data))
        logger.info(f"Security scan completed for {artifact['id']}")


class DeploymentService:
    """Container deployment service"""


    def __init__(self, broker: EventBroker):
        self.broker = broker
        # Subscribe to successful test events
        asyncio.create_task(
            self.broker.subscribe(
                ["dev.cdevents.testcase.finished.0.1.1"], 
                self.handle_test_finished
            )
        )

    async def handle_test_finished(self, event: CDEvent):
        """Handle test completion events"""
        test_data = event.data
        if test_data.test["outcome"] == "pass":
            await self.deploy_container(test_data.artifact, "staging")

    async def deploy_container(self, artifact: Dict[str, Any], environment: str):
        """Deploy container to specified environment"""
        deployment_id = str(uuid.uuid4())
        
        # Emit deployment started event
        context = CDEventContext(
            source="deployment.example.com",
            type="dev.cdevents.environment.created.0.1.1",
            subject=f"deployment/{deployment_id}"
        )
        
        deployment_data = DeploymentData(
            deployment={
                "id": deployment_id,
                "status": "started"
            },
            artifact=artifact,
            environment={
                "id": environment,
                "name": environment,
                "type": "development" if environment == "staging" else "production"
            }
        )
        
        await self.broker.publish(CDEvent(context, deployment_data))
        
        # Simulate deployment
        logger.info(f"Deploying {artifact['id']} to {environment}")
        await asyncio.sleep(1)
        
        # Emit deployment finished event
        context.type = "dev.cdevents.environment.modified.0.1.1"
        deployment_data.deployment["status"] = "completed"
        
        await self.broker.publish(CDEvent(context, deployment_data))
        logger.info(f"Deployment completed: {artifact['id']} in {environment}")


class PipelineOrchestrator:
    """Main pipeline orchestrator"""

    def __init__(self):
        self.broker = InMemoryEventBroker()
        self.repository_service = RepositoryService(self.broker)
        self.build_service = BuildService(self.broker)
        self.security_service = SecurityScanService(self.broker)
        self.deployment_service = DeploymentService(self.broker)
        
        # Subscribe to all events for monitoring
        asyncio.create_task(
            self.broker.subscribe(["*"], self.monitor_events)
        )

    async def monitor_events(self, event: CDEvent):
        """Monitor all pipeline events"""
        logger.info(f"Pipeline Event: {event.context.type} - {event.context.subject}")

    async def run_pipeline(self):
        """Simulate a complete pipeline run"""
        logger.info("Starting pipeline simulation...")
        
        # Simulate code push
        await self.repository_service.simulate_code_push(
            "https://git.example.com/my-org/my-app",
            "abc123def456"
        )
        
        # Wait for pipeline to complete
        await asyncio.sleep(5)
        
        logger.info("Pipeline simulation completed!")
        
        # Print event history
        print("\n--- Event History ---")
        for i, event in enumerate(self.broker.events, 1):
            print(f"{i}. {event.context.type}")
            print(f"   Subject: {event.context.subject}")
            print(f"   Time: {event.context.time}")
            print()
```

# Example usage

```python
async def main():
    """Run the pipeline example"""
    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline()

if __name__ == __main__:
   asyncio.run(main())
```

Example Build CDEvent

```json
{
    "specversion": "1.0",
    "id": "271069a8-fc18-44f1-b38f-9d70a1695819",
    "source": "https://cd.example.com/build-system",
    "type": "dev.cdevents.taskrun.finished.0.1.1",
    "subject": "builds/my-app/12345",
    "time": "2025-08-20T14: 30: 25.123456Z",
    "datacontenttype": "application/json",
    "data": {
        "context": {
            "version": "0.4.0",
            "id": "271069a8-fc18-44f1-b38f-9d70a1695819",
            "timestamp": "2025-08-20T14: 30: 25.123456Z",
            "links": {
                "pipelineRun": "https://cd.example.com/pipelines/pr-456789",
                "trigger": "https://github.com/my-org/my-app/commit/a1b2c3d4e5f6"
            }
        },
        "subject": {
            "id": "builds/my-app/12345",
            "type": "taskRun",
            "content": {
                "taskName": "build-container-image",
                "url": "https://cd.example.com/builds/my-app/12345",
                "outcome": "success",
                "errors": null,
                "reason": "Container image built successfully"
            }
        },
        "customData": {
            "buildSystem": "tekton",
            "buildDuration": "2m34s",
            "buildNode": "build-node-03",
            "buildSteps": [
                {
                    "name": "git-clone",
                    "status": "completed",
                    "duration": "12s",
                    "exitCode": 0
                },
                {
                    "name": "build-image",
                    "status": "completed",
                    "duration": "2m15s",
                    "exitCode": 0,
                    "image": "docker: 24.0.5",
                    "command": "docker build -t my-app:a1b2c3d ."
                },
                {
                    "name": "push-image",
                    "status": "completed",
                    "duration": "7s",
                    "exitCode": 0,
                    "registry": "registry.example.com"
                }
            ],
            "source": {
                "repository": "https://github.com/my-org/my-app",
                "branch": "main",
                "commit": "a1b2c3d4e5f6789012345678901234567890abcd",
                "author": "jane.developer@example.com"
            },
            "artifacts": [
                {
                    "id": "registry.example.com/my-app:a1b2c3d@sha256: 742c4b6f6b4d4f4e4d4c4b4a4948474645464544434241403938373635343332",
                    "type": "container-image",
                    "name": "my-app",
                    "digest": "sha256: 742c4b6f6b4d4f4e4d4c4b4a4948474645464544434241403938373635343332",
                    "tags": [
                        "my-app:a1b2c3d",
                        "my-app:latest",
                        "my-app:main"
                    ],
                    "size": 234567890,
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "registry": {
                        "url": "registry.example.com",
                        "namespace": "my-org"
                    },
                    "createdAt": "2025-08-20T14: 30: 23.456789Z",
                    "signature": {
                        "keyId": "cosign-key-1",
                        "algorithm": "ECDSA-P256-SHA256"
                    }
                }
            ],
            "environment": {
                "platform": "linux/amd64",
                "buildArgs": {
                    "NODE_VERSION": "18.17.0",
                    "APP_ENV": "production"
                },
                "labels": {
                    "org.opencontainers.image.source": "https://github.com/my-org/my-app",
                    "org.opencontainers.image.revision": "a1b2c3d4e5f6789012345678901234567890abcd",
                    "org.opencontainers.image.created": "2025-08-20T14: 30: 23.456789Z",
                    "org.opencontainers.image.title": "my-app",
                    "org.opencontainers.image.vendor": "My Organization"
                }
            },
            "security": {
                "scanResults": {
                    "vulnerabilities": {
                        "critical": 0,
                        "high": 1,
                        "medium": 3,
                        "low": 7,
                        "unknown": 0
                    },
                    "scanTime": "2025-08-20T14: 30: 24.789012Z",
                    "scanner": "trivy-v0.44.0"
                },
                "sbom": {
                    "format": "spdx-json",
                    "url": "https://artifacts.example.com/sbom/my-app-a1b2c3d.spdx.json"
                }
            }
        }
    }
}

```

## Explanation 

Let me break down this CDEvents build event and explain each component:

### Event Structure Overview

This is a **`dev.cdevents.taskrun.finished.0.1.1`** event representing a completed container build task. It follows both the CloudEvents specification (outer structure) and CDEvents specification (data content).

### CloudEvents Headers

**`specversion`**: CloudEvents specification version (1.0)
**`id`**: Unique identifier for this specific event instance
**`source`**: The system that generated this event (build system URL)
**`type`**: CDEvents type indicating a finished task run
**`subject`**: Resource identifier for the build job
**`time`**: When the event was generated
**`datacontenttype`**: Format of the event payload

### CDEvents Core Data

#### Context Section

Contains CDEvents-specific metadata including version, timestamp, and important links:

- **`links.pipelineRun`**: References the broader pipeline this build belongs to
- **`links.trigger`**: Points back to what triggered this build (the Git commit)

#### Subject Section

Describes the build task itself:

- **`outcome`**: Whether the build succeeded or failed
- **`reason`**: Human-readable explanation of the result
- **`url`**: Where to find detailed build logs and information

### Custom Data Section

This is where the real value lies for container builds:

#### Build Execution Details

- **Build system used** (Tekton in this case)
- **Duration and performance metrics**
- **Step-by-step breakdown** showing each build phase with timings and exit codes
- **Infrastructure details** like which build node was used

#### Source Information

Complete traceability back to the source code:

- Repository URL, branch, and exact commit SHA
- Author information for audit trails

#### Artifact Details

Comprehensive container image metadata:

- **Full image reference** with registry, name, tag, and content digest
- **Multiple tags** applied to the same image
- **OCI-compliant metadata** including media type and size
- **Security signatures** for supply chain verification

#### Environment Context

Build-time configuration captured for reproducibility:

- **Platform target** (linux/amd64)
- **Build arguments** used during container creation
- **OCI labels** applied to the image for metadata

#### Security Integration

Modern container builds include security scanning:

- **Vulnerability counts** by severity level
- **SBOM (Software Bill of Materials)** location for dependency tracking
- **Scanner information** for audit purposes

### Why This Structure Matters

**Traceability**: You can trace from deployment issues back to exact source commits and build configurations

**Automation**: Downstream systems can automatically trigger based on build outcomes, security scan results, or specific artifact properties

**Compliance**: The detailed metadata supports regulatory requirements and security policies

**Debugging**: When issues occur, all the context needed for investigation is captured in the event

**Integration**: Other tools can consume these events without needing to understand the specific build system’s API

This event structure enables truly event-driven pipelines where each service can make intelligent decisions based on rich, standardized metadata rather than just simple success/failure notifications.​​​​​​​​​​​​​​​​

