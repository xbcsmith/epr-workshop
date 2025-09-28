# Workshop Session: CDEvents in Practice - Building Event-Driven CI/CD Pipelines

## Outline

### Understanding CDEvents Fundamentals

This workshop provides hands-on experience implementing CDEvents specification
within event-driven CI/CD pipelines. Participants explore CDEvents fundamentals
by cloning the specification repository and using command-line tools like jq to
inspect event structures and understand event correlation through links and
context relationships.

### Building Event-Driven Pipeline Components

The session progresses to building complete event-driven pipeline components
using Python, including services for repository changes, container builds,
security scanning, and deployments. Participants create in-memory event brokers
demonstrating publish-subscribe patterns and learn service decoupling through
standardized CDEvents communication.

### EPR Integration and Advanced Patterns

EPR integration covers creating event receivers with CDEvents JSON schema
validation, storing events using NVRPP identifiers, and building Go-based
watchers that consume CDEvents from Kafka topics. Advanced topics include
distributed tracing patterns, multi-tool pipeline integration, and real-world
container pipeline scenarios including security-first deployments and compliance
audit trails.

## Workshop Format

Interactive exercises combine theoretical understanding with extensive hands-on
practice. Each concept includes immediate practical implementation using
provided tools and frameworks. The session starts with simple event inspection
and filtering, progressing through complete event-driven services, and
culminating in complex pipeline orchestration scenarios. Participants work
through realistic container build and deployment scenarios encountered in
production environments.

## Key Learning Objectives

Master CDEvents specification structure, event types, and correlation patterns.
Develop ability to design and implement loosely coupled services using
event-driven communication. Gain proficiency with EPR integration for storing,
retrieving, and validating CDEvents. Build skills in event filtering,
transformation, and routing systems. Understand multi-tool integration
capabilities and migration strategies from existing pipelines to CDEvents-based
architectures.
