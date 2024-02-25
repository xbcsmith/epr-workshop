# Event Provenance Registry (EPR) Workflows

## Overview

Event Provenance Registry (EPR) facilitates seamless communication and
interaction between its components to ensure efficient event tracking and
processing. This document outlines the key workflows involving the EPR Server,
Database, CLI, and Watcher components.

## Workflows

### EPR Server: Storing Events in the Database

Initiation: Events are generated within the CI/CD pipeline or other systems.
Processing: The EPR Server receives these events and communicates with the
Database to store them securely.

### EPR CLI: Creating Events with the cli

Command Execution: Users utilize the EPR CLI to create events. Communication
with Server: EPR CLI communicates with the EPR Server to store the newly created
events.

### EPR CLI: Searching for Events with the cli

CLI Query: Users leverage the EPR CLI to search for specific events based on
various criteria. Server Interaction: The EPR CLI communicates with the EPR
Server to retrieve the requested event data.

### EPR Watcher: Watching Redpanda with the Watcher Microservice

Continuous Monitoring: The EPR Watcher monitors messages in Redpanda for events
of interest. Action Execution: Upon detecting relevant messages, the Watcher
performs predefined actions. Event Notification: The EPR Watcher sends an event
to the EPR Server, explaining the action taken.

## EPR Message Bus: Interacting with Redpanda

Messaging Interaction: Both the EPR Server and EPR Watcher interact with
Redpanda for sending and receiving messages. Data Propagation: Redpanda serves
as the communication backbone, ensuring seamless flow of messages between EPR
components.

## Conclusion

These workflows demonstrate the dynamic interplay between the EPR Server,
Database, CLI, and Watcher components, allowing for efficient event tracking,
storage, and action execution within the Event Provenance Registry system. The
integration with Redpanda further enhances communication capabilities, providing
a robust foundation for event-driven workflows in CI/CD and beyond.
