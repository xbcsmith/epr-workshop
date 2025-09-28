# Content and Process

## Session 1: Introduction to Event Driven Architecture

- Why use microservices in event driven architecture?
- What are Cloud Events?
- What are CDEvents?
- What is EPR and how does it fit in an event driven CI/CD system?

Exercise: Discuss how and why to build out event driven services. Setup the
tools and message bus (RedPanda) needed to run an event driven system locally.
We will also cover how RedPanda (Kafka alternative) works.

## Session 2: Introduction to Event Provenance Registry

- Setup and deploy Event Provenance Registry (EPR) server locally.
- Create a microservice to interact with EPR and events.
- Overview of the EPR Python SDK with examples.

Exercise: Deploy EPR, RedPanda, and Postgres locally. Create a microservice to
watch for events and another to produce events. Leverage the python SDK to
create, retrieve, and query events in the system.

## Session #3: CDEvents and SBOMs

- Create and store CDEvents in our new ecosystem.
- Discuss how to leverage CDEvents and events in general.
- Use EPR to store and retrieve SBOMs.

Exercise: Create CDEvents and SBOMs using them to create events in our system to
trigger actions for microservices.

## Session #4 EPR MCP Server

- Overview of MCP servers and how they can be used in event driven systems.
- Introduction to the EPR MCP Server.
- Expand our microservices to do more things.
- Wrap up.

Exercise: Write an MCP server to interact with EPR to provide us with incite
into the data and events we created.

## Why attend?

If you work on the architecture, security, and reliability of your teams
pipelines this workshop will help you understand how you can introduce
asynchronous events as triggers to accelerate velocity, improve auditability,
and increase interoperability in your pipelines. We might cover how to
responsibly add AI to your pipeline as well.

Attendee Takeaways

Answers for the following questions:

- What is Event Driven CI/CD and Provenance?
- Why do I want events and provenance?
- How can I speed up my pipelines?
- How can I improve my auditability of the actions in my pipelines?
- How can I create systems that are interoperable and use a common language?
- Where can I add agentic AI into my pipeline?

## Target Group and Requirements

## Audience

This workshop is designed for developers and DevOps professionals interested in
learning and implementing Event-Driven CI/CD pipelines. While not mandatory,
having a basic understanding of the following concepts will greatly benefit your
learning experience:

### Requirements

Bring your own unix environment. The workshop is geared towards a Linux
development environment. While Mac OS and WSL2 work fine most of the time none
of us have tried this in native Windows without WSL2.

The requirements for the workshop are as follows:

- Laptop
- Golang installed on participants' machines
- Python installed on participants' machines
- Docker installed and running on participants' machines
- Docker Compose installed on participants' machines
- Code editor (e.g., Visual Studio Code, Sublime Text, Vim, Not Emacs)
- Command line utilities including:
  - git
  - make
  - curl
  - jq
  - go
  - golangci-lint
  - docker

## Workshop: Building an Event-Driven CI/CD Provenance System

In this hands-on workshop participants will journey through the architecture of
an Event-Driven CI/CD Provenance System. We will not only cover microservice
architectures, but also asynchronous communication, data interoperability,
message specifications, and schema validation.

We will learn how to leverage Golang for service and CLI development, Docker for
seamless deployment, Redpanda as a Kafka-compatible message bus, and PostgreSQL
for efficient backend storage. The workshop uses the open-source project Event
Provenance Registry (EPR) as the central service to leverage these technologies.

Over the course of the session we will delve into the EPR codebase, work through
coding and building Golang services, discuss the theories of event driven
systems, cover some pitfalls, and examine the integration with Redpanda for
effective event propagation. At the end we will live code an MCP server to add
agentic AI to the system.

The workshop provides a valuable blend of theoretical understanding and hands-on
experience in the dynamic landscape of Event-Driven CI/CD architectures.

4 90 minute sessions for the full workshop. The workshop can be modified to fit
a smaller time slot.

First public delivery at DevOpsCon San Diego 2024

Attendee Takeaways

Answers for the following questions:

- What is Event Driven CI/CD and Provenance?
- Why do I want events and provenance?
- How can I speed up my pipelines?
- How can I improve my auditability of the actions in my pipelines?
- How can I create systems that are interoperable and use a common language?
- Where can I add agentic AI into my pipeline?
