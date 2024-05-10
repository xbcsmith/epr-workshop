# EPR Python CLI

## Overview

In this section we will cover the EPR Python CLI and how to use it.

## CLI Examples

Create an event receiver using the provided parameters:

```bash
eprcli create event-receiver --name foo-python-cli --version 1.0.0 --type dev.foo.python.cli --description "foo python cli event receiver" --schema "{}"
```

Search for an event receiver using the provided parameters:

```bash
eprcli search event-receiver --id 01HW3SZ8N3MXA9EWZZY4HSVVNK
```

Create a second event receiver using the provided parameters:

```bash
eprcli create event-receiver --name bar-python-cli --version 1.0.0 --type dev.bar.python.cli --description "bar python cli event receiver" --schema "{}"
```

Create an event receiver group using the provided parameters:

```bash
eprcli create event-receiver-group --name foo-bar-python-cli --version 1.0.0 --type dev.foo.bar.python.cli --description "foo bar python cli event receiver group" --event-receiver-ids 01HWN885Z4D680AAASH81G1KXF,01HWN8NB7F13NMNSJ1SFK831KZ
```

Create an event using the provided parameters:

```bash
eprcli create event --name foo --version 1.0.1 --release 2023.11.16 --platform-id x86_64-gnu-linux-40 --package rpm  --description "The Foo of Brixton" --payload '{"name": "foo"}' --success --event-receiver-id 01HW3SZ8N3MXA9EWZZY4HSVVNK
```

Search for an event using the provided parameters:

```bash
eprcli search event --id 01HQK4MD17NXY7XAQ4B7V32DRS
```

```bash
eprcli search event --name foo --version 1.0.1 --release 2023.11.16
```
