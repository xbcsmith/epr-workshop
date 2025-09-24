# Event Provenance Registry (EPR) Workshop Introduction

## Overview

Event Provenance Registry (EPR) serves as the centralized storage and management system for event-driven CI/CD architectures. While CloudEvents and CDEvents provide standardized event formats, and Redpanda delivers the messaging infrastructure, EPR functions as the audit trail and provenance tracking system that maintains immutable records of all pipeline activities. EPR stores events with their complete context, enabling compliance reporting, debugging workflows, and building sophisticated event-driven automation through its watcher framework.

## EPR in Event-Driven CI/CD Context

EPR bridges the gap between transient event streams and persistent audit requirements. When CI/CD pipelines emit CloudEvents or CDEvents through Redpanda topics, EPR captures these events along with their metadata, payload, and relationships to other events. This creates an immutable audit trail that supports regulatory compliance, incident investigation, and pipeline analytics while enabling real-time event processing through its watcher components.

The system organizes events using Event Receivers that define schemas and categorization rules, while Event Receiver Groups provide higher-level organizational structures. Events are uniquely identified using the NVRPP (Name, Version, Release, Platform ID, Package) scheme inspired by RPM NEVRA format, enabling precise tracking of pipeline artifacts through their entire lifecycle.

## Core EPR Architecture

EPR consists of four main components that work together to provide comprehensive event management. The EPR Server handles REST and GraphQL APIs for event storage and retrieval, interfacing with a PostgreSQL database that maintains immutable event records. The EPR CLI provides command-line tools for creating events, searching historical data, and managing receivers and groups. The Watcher framework monitors Redpanda message streams, executes custom logic based on event patterns, and generates new events describing the actions taken.

This architecture enables both real-time event processing and historical analysis. Events flow from producers through Redpanda topics into EPR storage, where they become available for queries, analytics, and watcher-based automation. The combination of persistent storage and real-time processing capabilities makes EPR suitable for both compliance-focused audit trails and responsive pipeline automation.

## Session Overview

This workshop covers EPR deployment, configuration, and integration with the event-driven systems explored in previous sessions. You will examine the EPR codebase structure, understanding how the server, CLI, and watcher components interact with each other and with external systems like PostgreSQL and Redpanda.

The session includes hands-on work with EPR data structures, creating and managing Event Receivers with JSON schema validation, and implementing Event Receiver Groups for organizing related events. You will work with the NVRPP identifier system for tracking pipeline artifacts and understand how EPR maintains relationships between related events.

Practical exercises demonstrate building watchers that consume events from Redpanda, process them according to custom business logic, and generate new events that feed back into the EPR system. This creates closed-loop automation where pipeline activities automatically trigger responsive actions while maintaining complete audit trails.

The workshop concludes with EPR integration patterns that connect CloudEvents producers, CDEvents consumers, and Redpanda message streams into cohesive event-driven architectures. You will understand how EPR's persistence and querying capabilities enable sophisticated pipeline analytics, compliance reporting, and debugging workflows that are essential for production CI/CD systems.