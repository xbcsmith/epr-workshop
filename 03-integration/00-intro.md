# Intro to Redpanda Integration

## Overview

This workshop session introduces Redpanda, a modern event streaming platform
designed for real-time data processing and event-driven CI/CD architectures.

Redpanda provides infrastructure for streaming real-time data through a single
binary that includes a built-in schema registry, HTTP proxy, and message broker,
where producers send events that Redpanda stores in sequence and organizes into
topics. Unlike traditional solutions that require complex multi-component
deployments, Redpanda simplifies event streaming infrastructure while delivering
high performance and Kafka API compatibility.

---

## Redpanda Core Architecture

### Event Streaming Fundamentals

Redpanda is an event streaming platform that provides infrastructure for
streaming real-time data, where producers are client applications that send data
to Redpanda in the form of events. Events represent state changes or significant
occurrences within systems, and Redpanda ensures these events are durably
stored, properly ordered, and made available for consumption by multiple
subscribers.

The platform organizes events into topics, which serve as logical channels for
related event streams. Each topic maintains events in an immutable, append-only
log that enables replay capabilities essential for event sourcing patterns and
system recovery scenarios.

---

### Performance and Design Philosophy

Redpanda's engine is written in modern C++ for raw speed and efficiency, with a
single self-contained binary that has no external dependencies or JVM overhead.
This design eliminates the operational complexity typically associated with
distributed streaming platforms while delivering superior performance
characteristics.

Conceptually similar to Apache Kafka but much easier to install, monitor, and
manage, Redpanda can achieve extremely high performance with high fault
tolerance while using less computing and memory resources. This efficiency makes
Redpanda particularly suitable for resource-constrained environments and
cost-conscious deployments.

---

### Kafka Compatibility and Migration

Built on the Kafka protocol, Redpanda delivers low-latency, high-throughput
streaming data processing, making it ideal for building real-time applications.
The platform maintains full API compatibility with Apache Kafka, enabling
seamless migration of existing Kafka-based applications without code changes.

This compatibility extends to client libraries, monitoring tools, and
integration patterns, allowing organizations to leverage existing Kafka
ecosystem investments while gaining Redpanda's operational advantages.

---
