# Event Provenance Registry (EPR) Concepts

## Overview

Event Provenance Registry (EPR) provides a centralized, secure, and efficient
means to track and process events. This document outlines the key concepts
involved in the EPR system.

---

## Components

### Server

Responsible for managing, storing, and processing events.

### Database

Stores events for retrieval and historical tracking.

### CLI

Command-line interface for creating and searching events in the EPR Server.

### Watcher

Monitors messages in Redpanda, takes actions, and sends event notifications to
the EPR Server.

### Message Bus

Interacts with Redpanda for sending and receiving messages.

---

## Data Structures

### Events

Events are the fundamental data structure in EPR. They represent the core data
entities and act as the foundational building blocks of the provenance tracking
system.

---

#### Event Data Structures

EPR employs a structured set of data attributes to capture and represent events
within its system. Each event created in EPR is uniquely identified and
characterized by various key attributes. Below is an overview of these essential
data elements:

**ID**: A unique identifier assigned to each event upon its creation in EPR.

**Name**: The name of the event, provided by the creator of the event.

**Version**: The version of the event, specified by the creator.

**Release**: The release of the event, determined by the creator.

**PlatformID**: The platform ID associated with the event, provided by the
creator.

**Package**: The package to which the event pertains, supplied by the creator.

**Payload**: The payload of the event, containing additional data relevant to
the event's context.

**Success**: The success status of the event, indicating whether the event was
successful or not.

**EventReceiverID**: The ID of the event receiver associated with the event,
provided by the creator.

**CreatedAt**: The timestamp representing the time when the event was created in
EPR.

**EventReceiver**: The event receiver object assigned to the event upon creation
in EPR.

---

#### NVRPP Identifier

A crucial aspect of event identification in EPR is the NVRPP identifier,
standing for Name, Version, Release, Platform ID, and Package. These five keys
collectively form a unique identifier for an event within the pipeline. The
NVRPP serves as a tracking mechanism, allowing for the association of events
with specific units in the pipeline. This identifier is particularly significant
for receipts, enabling a comprehensive understanding of events within a specific
context.

NVRPP Example:

```text
Name: foo
Version: 1.0.0
Release: 2023
Platform ID: aarch64-oci-linux-2
Package: docker
```

The structure of the NVRPP is inspired by the RPM NEVRA format, providing a
standardized and consistent way to identify and categorize events within the EPR
system.

---

### Event Receivers

Event receivers are structures within EPR designed to capture and categorize
events. They define the scope and nature of events they are interested in. Event
receivers represent an action that occured in the pipeline.

#### Event Receiver Data Structures

**ID**: A unique identifier assigned to each event receiver upon its creation in
EPR.

**Name**: The name of the event receiver, provided by the creator.

**Version**: The version of the event receiver, specified by the creator.

**Type**: The type of event receiver, determined by the creator.

**Description**: A description of the event receiver, provided by the creator.

**Schema**: The schema of the event receiver, provided by the creator.

**Fingerprint**: The fingerprint of the event receiver, created by EPR when the
event receiver is initialized.

**CreatedAt**: The timestamp representing the time when the event receiver was
created in EPR.

---

### Event Receiver Groups

Event receiver groups provide a higher-level organizational structure within
EPR. Event receiver groups are used to group multiple event receivers.

#### Event Receiver Group Data Structures

**ID**: A unique identifier assigned to each event receiver group upon its
creation in EPR.

**Name**: The name of the event receiver group, provided by the creator.

**Version**: The version of the event receiver group, specified by the creator.

**Type**: The type of event receiver group, determined by the creator.

**Description**: A description of the event receiver group, provided by the
creator.

**Enabled**: The enabled status of the event receiver group, determined by the
creator.

**EventReceiverIDs**: The IDs of the event receivers associated with the event
receiver group.

**CreatedAt**: The timestamp representing the time when the event receiver group
was created in EPR.

**UpdatedAt**: The timestamp representing the time when the event receiver group
was last updated in EPR.

---
