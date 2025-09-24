# Workshop Session: CloudEvents with EPR

## Outline

### Understanding CloudEvents Fundamentals

This workshop provides hands-on experience using CloudEvents with the Event Provenance Registry (EPR). Participants explore CloudEvents specification structure, learning core attributes like `id`, `source`, `type`, `specversion`, `time`, `datacontenttype`, and `data`. The session covers CloudEvents SDK usage by cloning the Python SDK repository, setting up virtual environments, and running sample client-server applications to understand event production and consumption patterns.

### Creating and Testing CloudEvents

Participants work with practical CloudEvents creation using the Python SDK, implementing Flask-based servers that receive CloudEvents and clients that send structured events. The session includes running pytest tests to validate CloudEvents functionality and exploring different encoding formats. Hands-on exercises demonstrate event interoperability across different transport protocols and encoding methods.

### EPR Integration for CloudEvents Storage

The workshop progresses to EPR integration, covering event receiver creation with CloudEvents schema validation, storing CloudEvents as EPR event payloads, and retrieving events using both REST API calls and epr-cli commands. Participants learn to embed CloudEvents JSON within EPR events, query stored events, and organize CloudEvents using Event Receivers for efficient event management and provenance tracking.

## Workshop Format

Interactive exercises combine CloudEvents specification exploration with practical implementation using Python SDK samples. Each section includes immediate hands-on practice with running code examples, from basic event creation to complete client-server scenarios. Participants work through realistic event-driven scenarios, including schema validation, event persistence, and querying patterns using both curl commands and EPR CLI tools.

## Key Learning Objectives

Master CloudEvents specification structure and core attributes for event interoperability. Develop proficiency with CloudEvents Python SDK for creating producers and consumers. Gain skills in EPR integration for CloudEvents storage, validation, and retrieval. Understand event schema design, versioning strategies, and organized event management using Event Receivers for provenance and auditing workflows.
