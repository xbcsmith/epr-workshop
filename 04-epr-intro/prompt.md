# Prompt

Write a workshop session for the following list of topics:

Exploring EPR: Codebase Overview

- Get the Code
- Overview of the project structure
- Understanding the role of each component (server, CLI, client)

Write a document describing EPR workflows for the Workshop based on the
following

- The "EPR Server" communicates with the "Database" for storing events.
- The "EPR CLI" creates events in the "EPR Server."
- THe "EPR CLI" searches for events in the "EPR Server."
- The "EPR Watcher" watches for messages in "Redpanda". The "EPR Watcher" uses
  the message to do something. The "EPR Watcher" sends and event explaining the
  action to the "EPR Server."
- Both the "EPR Server" and "EPR Watcher" interact with "Redpanda" for sending
  and receiving messages.
