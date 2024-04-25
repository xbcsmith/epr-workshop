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

Create an event using the provided parameters:

```bash
eprcli create event --name foo --version 1.0.1 --release 2023.11.16 --description "The Foo of Brixton" --payload '{"name": "foo"}' --success true --event-receiver-id 01HW3SZ8N3MXA9EWZZY4HSVVNK
```

Search for an event using the provided parameters:

````bash
eprcli search event --id 01HQK4MD17NXY7XAQ4B7V32DRS
```w

```bash
eprcli search event --name foo --version 1.0.1 --release 2023.11.16
````
