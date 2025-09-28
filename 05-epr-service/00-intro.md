# Intro to EPR Service

## Overview

This section introduces the Event Provenance Registry (EPR) service used
throughout the workshop. The EPR is a small HTTP service that records and
indexes events emitted by CI/CD systems and other automated tools. Events are
classified by event receivers and grouped into event receiver groups; the
service also publishes messages to a message broker so downstream consumers can
react to event state changes.

You'll learn how to:

- Start the backend dependencies (message broker and database).
- Create and manage event receivers and receiver groups.
- Send events to the registry via the REST API (curl examples included).
- Inspect and query events and their metadata.

This section is hands-on and assumes you have a terminal and Docker available.
Follow the linked pages in this folder for step-by-step commands and examples.

---

## What you will run in this section

1. Start the service dependencies (Redpanda and PostgreSQL) using Docker
   Compose.
2. (Initial setup) Create the Kafka/Redpanda topic the service will publish to.
3. Use the REST API to create:
   - an Event Receiver (classification + schema)
   - an Event
   - an Event Receiver Group
4. Query the service for created resources and inspect stored events.

---

## Requirements

- Golang 1.24+ (for building/running EPR service from source)
- Docker and Docker Compose (for the Redpanda broker, Postgres DB and other
  dependencies)
- jq (optional, helpful for inspecting JSON)

---

## Ports & URLs used in the exercises

- EPR REST API (service): http://localhost:8042
- Redpanda admin console: http://localhost:8080/overview
- Redpanda broker (default in examples): localhost:19092
- Default topic used in workshop examples: `epr.dev.events`

---

## Where to go next

- Start dependencies: `01-backend.md` (launch Redpanda, Postgres, create topic)
- Build & run the EPR service from source: see `02-build.md` (if present) or the
  workshop root README for build instructions.
- Hands-on REST API examples: `03-curl.md` (create receivers, events, groups,
  queries)

---
