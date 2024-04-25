# Start the Backend Services

## Introduction

This section guides you through the process of initiating the backend services
essential for working with EPR. Docker Compose will be employed to launch these
services, with Redpanda serving as the message broker for event transmission and
PostgreSQL as the designated database for data storage.

## Requirements

- [Golang 1.21+](https://go.dev/dl/)
- [Docker](https://docs.docker.com/engine/install)
- [Docker-Compose](https://docs.docker.com/engine/install)

## Start Dependencies

Utilize the provided docker-compose file to launch the required dependencies,
including a PostgreSQL database, a Redpanda Kafka instance, and a Redpanda UI.
Execute the following command:

```bash
docker compose -f ./docker-compose.services.yaml up
```

Access the Redpanda admin console at `http://localhost:8080/overview`

Create a Topic (Only necessary for initial setup)

Either use the admin console to create a topic named "epr.dev.events" or employ
the Docker container with the following command:

```bash
docker exec -it redpanda \
    rpk topic create epr.dev.events --brokers=localhost:19092
```
