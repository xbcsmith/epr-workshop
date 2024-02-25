Diagram to represent an Event Provenance Registry (EPR) workflow:

```mermaid
graph TD;

    A[EPR Server] --> M[Message] --> C[Redpanda];
    A[EPR Server] <--> X[Event] <--> B[Database];
    A[EPR Server] --> Q[Event] --> K[EPR CLI];
    L[EPR CLI] --> Y[Event] --> A[EPR Server];
    W[EPR Watcher] <--> N[Message] <--> C[Redpanda];
    W[EPR Watcher] --> D[Do Something] --> Z[Event] --> A[EPR Server];
    style A fill:#005493,stroke:#cccccc,stroke-width:2px;
    style B fill:#0096ff,stroke:#cccccc,stroke-width:2px;
    style C fill:#ff2600,stroke:#cccccc,stroke-width:2px;
    style D fill:#ff9300,stroke:#cccccc,stroke-width:2px;
    style L fill:#942193,stroke:#cccccc,stroke-width:2px;
    style K fill:#942193,stroke:#cccccc,stroke-width:2px;
    style M fill:#7a81ff,stroke:#cccccc,stroke-width:2px;
    style N fill:#7a81ff,stroke:#cccccc,stroke-width:2px;
    style Q fill:#008f00,stroke:#cccccc,stroke-width:2px;
    style W fill:#531b93,stroke:#cccccc,stroke-width:2px;
    style X fill:#008f00,stroke:#cccccc,stroke-width:2px;
    style Y fill:#008f00,stroke:#cccccc,stroke-width:2px;
    style Z fill:#008f00,stroke:#cccccc,stroke-width:2px;
```

In this diagram:

- The "EPR Server" communicates with the "Database" for storing events.
- The "EPR CLI" creates events in the "EPR Server."
- The "EPR Watcher" watches for messages in "Redpanda". The "EPR Watcher" uses
  the message to do something. The "EPR Watcher" sends and event explaining the
  action to the "EPR Server."
- Both the "EPR Server" and "EPR Watcher" interact with "Redpanda" for sending
  and receiving messages.
