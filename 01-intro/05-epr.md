# Event Provenance Registry (EPR): A Detailed Overview

## Overview

The Event Provenance Registry (EPR) is designed with simplicity at its core,
though its operation may benefit from a comprehensive understanding. At a high
level, EPR serves as a centralized system that systematically captures events
stemming from tasks executed within a pipeline. These events are subsequently
dispatched to a designated message queue. EPR introduces the concept of
"watchers", additional services that monitor the message queue for events of
particular interest. Upon detecting such events, the watcher executes predefined
logic. For instance, a typical watcher might activate webhooks upon recognizing
particular events.

---

## Functionality

EPR possesses the capability to gate events based on specified criteria,
offering a level of control over the types of events that are processed. This
gating mechanism enhances the flexibility and adaptability of the system to meet
diverse use cases. EPR seamlessly integrates with both Redpanda and Kafka, two
prominent message queue systems, providing users with the flexibility to choose
their preferred messaging infrastructure.

To facilitate the organized collection of events, EPR employs three key data
structures:

---

## Data Structures

### Events

Events represent the core data entities within EPR. An event is simply a record
of something changing state. These entities encapsulate information about tasks
executed in the pipeline. Events are created to represent a set of event_types
that are performed on a unit. Events act as the foundational building blocks of
the provenance tracking system.

---

### Event Receivers

Event receivers are structures within EPR designed to capture and categorize
events. They act as recipients of specific events, defining the scope and nature
of events they are interested in. These receivers streamline the categorization
and handling of events based on predetermined criteria. Event Receivers are
reusable lists of requirements. When an event receiver receives an event, it
publishes a message that specifies the type of event.

---

### Event Receiver Groups

Event receiver groups are collections of event receivers. Event receiver groups
provide a higher-level organizational structure within EPR. By grouping multiple
event receivers, users can efficiently manage and coordinate the processing of
events across various categories or functional units. This grouping mechanism
enhances the scalability and modularity of event handling.

When all event_receivers in an event_receiver_group have successful events (with
"success": true status), the event_receiver_group publishes a message that
specifies an event_type for the event_receiver_group.

An event_receiver_group can be enabled or disabled (with "enabled": true|false).
When enabled, the event_receiver_group acts as previously described. When
disabled, messages for the event_receiver_group will not be published. Messages
will still be published for the underlying event_receivers should they receive
successful events.

---

## Conclusion

In practical terms, EPR serves as a powerful tool for orchestrating event-driven
architectures, allowing users to track, categorize, and respond to events in a
streamlined and efficient manner. The support for Redpanda and Kafka, along with
the well-defined data structures, makes EPR a versatile and adaptable solution
for a wide range of event-driven scenarios.

---

## Links

- [Event Provenance Registry](https://github.com/sassoftware/event-provenance-registry)
- [EPR Documentation](https://github.com/sassoftware/event-provenance-registry/blob/master/docs/README.md)
- [EPR Workshop](https://github.com/xbcsmith/epr-workshop)
- [EPR Python Client](https://github.com/xbcsmith/epr-python)
- [EPR MCP Server](https://github.com/xbcsmith/epr-mcp-python)

---
