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
        "type": "dev.cdevents.artifact.packaged.0.2.0",
        "subject": "registry.example.com/my-app:abc123",
        "time": datetime.utcnow().isoformat() + "Z",
        "data": {"artifact": {"id": "registry.example.com/my-app:abc123", "digest": "sha256:aaaaaaaa..."}},
    }

    await broker.publish(event)


if __name__ == "__main__":
    asyncio.run(main())
