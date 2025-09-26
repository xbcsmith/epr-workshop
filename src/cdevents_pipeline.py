import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CDEventContext:
    """CDEvents context following the specification"""

    version: str = "0.4.1"
    id: str = ""
    chainId: str = ""
    source: str = ""
    type: str = ""
    timestamp: str = ""
    schemaUri: Optional[str] = None
    links: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.chainId:
            self.chainId = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class CDEventSubject:
    """CDEvent subject following the specification"""

    id: str
    source: str
    type: str
    content: Dict[str, Any]


class CDEvent:
    """CDEvent wrapper following the specification"""

    def __init__(self, context: CDEventContext, subject: CDEventSubject):
        self.context = context
        self.subject = subject

    def to_dict(self) -> Dict[str, Any]:
        """Convert to CDEvents format"""
        return {"context": asdict(self.context), "subject": asdict(self.subject)}

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


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


class RepositoryService:
    """Simulates a Git repository service"""

    def __init__(self, broker: EventBroker):
        self.broker = broker

    async def simulate_code_push(self, repo_url: str, commit_sha: str):
        """Simulate a code push event"""
        context = CDEventContext(source="/event/source/git", type="dev.cdevents.repository.modified.0.2.0")

        subject = CDEventSubject(
            id=f"repo/{commit_sha}",
            source="/event/source/git",
            type="repository",
            content={"name": "my-app", "owner": "my-org", "url": repo_url, "viewUrl": repo_url},
        )

        event = CDEvent(context, subject)
        await self.broker.publish(event)
        logger.info(f"Code pushed to {repo_url}, commit: {commit_sha}")


class BuildService:
    """Container build service"""

    def __init__(self, broker: EventBroker):
        self.broker = broker

    async def initialize(self):
        """Initialize subscriptions"""
        await self.broker.subscribe(["dev.cdevents.repository.modified.0.2.0"], self.handle_repository_change)

    async def handle_repository_change(self, event: CDEvent):
        """Handle repository change events"""
        logger.info(f"Build service handling repository change: {event.subject.id}")
        await self.start_build(event.subject.content["url"], event.subject.id, event.context.chainId)

    async def start_build(self, repo_url: str, repo_id: str, chain_id: str):
        """Start container build process"""
        build_id = str(uuid.uuid4())

        # Simulate build process
        logger.info(f"Building container for repository {repo_id}")
        await asyncio.sleep(2)  # Simulate build time

        # Build completed - emit build finished event
        image_digest = f"sha256:{'a' * 64}"  # Simulated digest
        artifact_id = f"pkg:oci/my-app@{image_digest}"

        context = CDEventContext(
            source="/event/source/build",
            type="dev.cdevents.build.finished.0.2.0",
            chainId=chain_id,
        )

        subject = CDEventSubject(
            id=f"build/{build_id}", source="/event/source/build", type="build", content={"artifactId": artifact_id}
        )

        await self.broker.publish(CDEvent(context, subject))
        logger.info(f"Build finished: {artifact_id}")


class SecurityScanService:
    """Container security scanning service"""

    def __init__(self, broker: EventBroker):
        self.broker = broker

    async def initialize(self):
        """Initialize subscriptions"""
        await self.broker.subscribe(["dev.cdevents.build.finished.0.2.0"], self.handle_build_finished)

    async def handle_build_finished(self, event: CDEvent):
        """Handle build finished events"""
        logger.info(f"Security service handling build finished: {event.subject.id}")
        artifact_id = event.subject.content["artifactId"]
        await self.scan_container(artifact_id, event.context.chainId)

    async def scan_container(self, artifact_id: str, chain_id: str):
        """Perform security scan on container"""
        scan_id = str(uuid.uuid4())

        logger.info(f"Starting security scan for {artifact_id}")

        # Simulate scanning
        await asyncio.sleep(1)

        # Emit test finished event
        context = CDEventContext(
            source="/event/source/security", type="dev.cdevents.testsuiterun.finished.0.2.0", chainId=chain_id
        )

        subject = CDEventSubject(
            id=f"scan/{scan_id}",
            source="/event/source/security",
            type="testSuiteRun",
            content={
                "testSuite": {"id": scan_id, "name": "security-scan"},
                "outcome": "pass",
                "artifactId": artifact_id,
            },
        )

        await self.broker.publish(CDEvent(context, subject))
        logger.info(f"Security scan completed for {artifact_id}")


class DeploymentService:
    """Container deployment service"""

    def __init__(self, broker: EventBroker):
        self.broker = broker

    async def initialize(self):
        """Initialize subscriptions"""
        await self.broker.subscribe(["dev.cdevents.testsuiterun.finished.0.2.0"], self.handle_test_finished)

    async def handle_test_finished(self, event: CDEvent):
        """Handle test completion events"""
        logger.info(f"Deployment service handling test finished: {event.subject.id}")
        if event.subject.content["outcome"] == "pass":
            artifact_id = event.subject.content["artifactId"]
            await self.deploy_container(artifact_id, "staging", event.context.chainId)

    async def deploy_container(self, artifact_id: str, environment: str, chain_id: str):
        """Deploy container to specified environment"""
        deployment_id = str(uuid.uuid4())

        # Simulate deployment
        logger.info(f"Deploying {artifact_id} to {environment}")
        await asyncio.sleep(1)

        # Emit deployment finished event
        context = CDEventContext(
            source="/event/source/deployment", type="dev.cdevents.service.deployed.0.2.0", chainId=chain_id
        )

        subject = CDEventSubject(
            id=f"deployment/{deployment_id}",
            source="/event/source/deployment",
            type="service",
            content={"environment": {"id": environment}, "artifactId": artifact_id},
        )

        await self.broker.publish(CDEvent(context, subject))
        logger.info(f"Deployment completed: {artifact_id} in {environment}")


class PipelineOrchestrator:
    """Main pipeline orchestrator"""

    def __init__(self):
        self.broker = InMemoryEventBroker()
        self.repository_service = RepositoryService(self.broker)
        self.build_service = BuildService(self.broker)
        self.security_service = SecurityScanService(self.broker)
        self.deployment_service = DeploymentService(self.broker)

    async def initialize(self):
        """Initialize all service subscriptions"""
        await self.build_service.initialize()
        await self.security_service.initialize()
        await self.deployment_service.initialize()
        await self.broker.subscribe(["*"], self.monitor_events)

    async def monitor_events(self, event: CDEvent):
        """Monitor all pipeline events"""
        logger.info(f"Pipeline Event: {event.context.type} - {event.subject.id}")

    async def run_pipeline(self):
        """Simulate a complete pipeline run"""
        logger.info("Starting pipeline simulation...")

        # Initialize all subscriptions first
        await self.initialize()

        # Simulate code push - this should trigger the entire pipeline
        await self.repository_service.simulate_code_push("https://git.example.com/my-org/my-app", "abc123def456")

        # Wait for pipeline to complete - increased time to allow all async operations
        await asyncio.sleep(10)

        logger.info("Pipeline simulation completed!")

        # Print event history
        print("\n--- Event History ---")
        for i, event in enumerate(self.broker.events, 1):
            print(f"{i}. {event.context.type}")
            print(f"   Subject: {event.subject.id}")
            print(f"   Chain ID: {event.context.chainId}")
            print(f"   Timestamp: {event.context.timestamp}")
            print()


async def main():
    """Run the pipeline example"""
    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
