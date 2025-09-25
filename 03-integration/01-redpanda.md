# Redpanda Integration

Redpanda is a Kafka-compatible event streaming platform that provides a message
bus for our event-driven architecture.

## Overview of Redpanda

### Redpanda Nodes

Redpanda nodes are designed to be self-contained, with all necessary components
built-in. This eliminates the need for external dependencies (like JVM or
KRaft), resulting in rapid boot times, streamlined CI/CD integration, and
enhanced reliability in production environments.

### Redpanda Keeper (rpk)

Redpanda Keeper (rpk) is a powerful command line interface (CLI) tool for
managing and tuning your Redpanda clusters. This single binary can be installed
as a standalone tool, making it ideal for self-hosted setups, cloud deployments,
and Kubernetes environments.

### Redpanda Console

Redpanda Console is a user-friendly UI for managing your Redpanda or other
Kafka-compatible clusters. It offers comprehensive Kafka administration,
improved data observability, and robust security features, including SSO, RBAC,
and Kerberos support.Setting Up Redpanda: Single Node Deployment

## Single Node Deployment

To begin with, let's deploy Redpanda as a single node, and we'll guide you
through the process of consuming and producing messages. Follow these steps:

### Step 1: Start Redpanda in a Docker Container

Execute the following command to initiate Redpanda in a single Docker container.
This command ensures that Redpanda runs in the background. Remember to stop the
container once you've completed your development tasks.

```bash
docker run --pull=always --name=redpanda-0 --rm \
    -p 8081:8081 \
    -p 8082:8082 \
    -p 9092:9092 \
    -p 9644:9644 \
    docker.redpanda.com/redpandadata/redpanda:latest \
    redpanda start \
    --overprovisioned \
    --smp 1  \
    --memory 1G \
    --reserve-memory 0M \
    --node-id 0 \
    --check=false
```

### Step 2: Create a Topic

Now, let's create a topic named `epr.dev.events`. Execute the following command
to create the topic within the running Redpanda container.

```bash
docker exec -it redpanda-0 \
  rpk topic create epr.dev.events --brokers=localhost:9092
```

### Step 3: Produce a Message

Produce a message into the `epr.dev.events` topic using the following command.
Type your desired text and press `Enter` to separate between messages. To exit
the produce command, press `Ctrl + C`.

```bash
docker exec -it redpanda-0 \
  rpk topic produce epr.dev.events --brokers=localhost:9092
```

### Step 4: Consume a Message

Finally, let's consume a message from the `epr.dev.events` topic. Execute the
following command, and each message will be displayed with its metadata.

```bash
docker exec -it redpanda-0 \
  rpk topic consume epr.dev.events --brokers=localhost:9092
```

The message output will be in JSON format, including details such as the message
content, partition, offset, and timestamp.

```json
{
  "message": "How do you stream with Redpanda?\n",
  "partition": 0,
  "offset": 1,
  "timestamp": "2021-02-10T15:52:35.251+02:00"
}
```

These steps demonstrate a straightforward single node deployment of Redpanda,
allowing you to create topics, produce messages, and consume them for your
development and testing purposes.

## Setting up Redpanda: Multi-Node Deployment

In this section we will delve into deploying Redpanda in a multi-node
configuration and explore the Redpanda admin console. Follow these steps:

### Step 1: Start Redpanda with Docker Compose

Navigate to the directory where you stored the file in a command prompt and
deploy Redpanda using Docker Compose.

```bash
docker compose -f ./compose/docker-compose.yaml up
```

This command runs a single Redpanda broker, configured without authentication,
accessible from `localhost:9092`. You can access the web console in your browser
at [http://localhost:8080/overview](http://localhost:8080/overview).

### Step 2: Create a Topic in Redpanda

Now, let's create a topic named `epr.dev.events`. Execute the following command
to create the topic within the running Redpanda container.

```bash
docker exec -it redpanda \
  rpk topic create epr.dev.events --brokers=localhost:9092
```

View the topic in the Redpanda admin console at
[http://localhost:8080/topics/epr.dev.events](http://localhost:8080/topics/epr.dev.events).

### Step 3: Produce a Message in Redpanda

Produce a message into the `epr.dev.events` topic using the following command.
Type your desired text and press `Enter` to separate messages. To exit the
produce command, press `Ctrl + C`.

```bash
docker exec -it redpanda \
  rpk topic produce epr.dev.events --brokers=localhost:9092
```

View the message in the Redpanda admin console (refresh the page if needed) at
[http://localhost:8080/topics/epr.dev.events](http://localhost:8080/topics/epr.dev.events).

### Step 4: Consume a Message from Redpanda

Finally, let's consume a message from the `epr.dev.events` topic. Execute the
following command, and each message will be displayed with its metadata.

```bash
docker exec -it redpanda-0 \
  rpk topic consume epr.dev.events --brokers=localhost:9092
```

The message output will be in JSON format, including details such as the message
content, partition, offset, and timestamp.

```json
{
  "topic": "epr.dev.events",
  "value": "here is my message",
  "timestamp": 1708809176859,
  "partition": 0,
  "offset": 0
}
```

These steps showcase a straightforward multi-node deployment of Redpanda,
enabling you to seamlessly create topics, produce messages, and consume them for
your development and testing needs.

## Documentation

- [What is Redpanda](https://redpanda.com/what-is-redpanda)
- [Redpanda documentation](https://docs.redpanda.com/docs/home/)
- [Install the Redpanda CLI](https://docs.redpanda.com/docs/get-started/rpk-install/)
- [Redpanda on GitHub](https://github.com/redpanda-data/redpanda/)
