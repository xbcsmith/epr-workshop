# Intro to CDEvents and EPR

## Overview

In this section we will cover the [CDEvents]() concepts and how to use them.

## Introduction

This session introduces the Continuous Delivery Core Events used throughout the workshop. We'll focus on the runtime events that orchestration systems emit to describe the lifecycle of pipelines and tasks. The aim is to give you a practical understanding of the two core subjects — `pipelineRun` and `taskRun` — and the common predicates (`queued`, `started`, `finished`) that describe their state transitions.

You'll learn how these low-level CDEvents map to real-world CI/CD systems, why they are useful for observability and automation, and how to use them in exercises later in the workshop (for example: detecting failed task runs, tracking pipeline progress across distributed workers, or correlating taskRuns to their parent pipelineRun). The remainder of this document defines the subjects, their fields, and the event types you'll use in the hands-on labs.

CDEvents is a standardization effort that defines a common vocabulary and format for describing Continuous Delivery events across different tools and platforms. It’s particularly useful in event-driven CI/CD pipelines for creating interoperable, observable, and loosely coupled systems.

## Core CDEvents Concepts

CDEvents provides standardized event schemas for common CI/CD activities like builds, deployments, tests, and releases. Each event follows a CloudEvents specification format and includes contextual information about what happened, when, and where in your pipeline.

## Architecture for Container-Focused Pipelines

In an event-driven CI/CD pipeline producing OCI containers, CDEvents typically flow through:

**Event Sources** → **Event Router/Broker** → **Event Consumers**

The event sources generate standardized CDEvents, a message broker (like Apache Kafka, NATS, or cloud pub/sub services) routes them, and consumers react to relevant events.

## Key CDEvents for Container Pipelines

For OCI container production, you’ll primarily work with these event types:

- **Repository events**: Source code changes that trigger builds
- **Build events**: Container image building started/finished
- **Test events**: Security scans, integration tests on containers
- **Artifact events**: Container registry pushes, vulnerability scan results
- **Deployment events**: Container deployments to staging/production environments

## Implementation Patterns

**1. Pipeline Orchestration**
Instead of rigid pipeline definitions, services listen for relevant CDEvents and trigger their operations. For example, a security scanning service listens for "artifact packaged" events and automatically scans newly built container images.

**2. Multi-Tool Integration**
CDEvents enable different tools to communicate without tight coupling. Your Jenkins build can emit standard events that trigger Tekton deployments, ArgoCD sync operations, or custom monitoring workflows.

**3. Observability and Auditing**
All pipeline activities generate standardized events, creating a comprehensive audit trail. You can build dashboards, alerts, and compliance reports by consuming these events.

## Example Event Flow

1. Developer pushes code → Repository emits "change merged" CDEvent
1. Build service consumes event → Builds container → Emits "artifact packaged" CDEvent
1. Security scanner consumes artifact event → Scans container → Emits "test finished" CDEvent
1. Deployment service consumes successful test event → Deploys container → Emits "deployment started/finished" CDEvents

## Implementation Considerations

**Event Schema Validation**: Ensure all tools emit properly formatted CDEvents according to the specification to maintain interoperability.

**Event Ordering and Reliability**: Use message brokers with ordering guarantees and implement retry logic for critical pipeline steps.

**Event Filtering**: Consumers should filter events based on context (environment, application, etc.) to avoid unnecessary processing.

**Backward Compatibility**: As your pipeline evolves, maintain event schema compatibility to avoid breaking existing consumers.

The key advantage of CDEvents in container pipelines is the decoupling it provides - each tool focuses on its core responsibility while communicating through standardized events, making your pipeline more resilient, observable, and easier to evolve over time.​​​​​​​​​​​​​​​​