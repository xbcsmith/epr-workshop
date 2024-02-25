# EPR Quickstart Guide

## Start the Backend Services

### Introduction

This section guides you through the process of initiating the backend services
essential for working with EPR. Docker Compose will be employed to launch these
services, with Redpanda serving as the message broker for event transmission and
PostgreSQL as the designated database for data storage.

## Requirements

- [Golang 1.21+](https://go.dev/dl/)
- [Docker](https://docs.docker.com/engine/install)
- [Docker-Compose](https://docs.docker.com/engine/install)

### Start Dependencies

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

## Building EPR Server

### Get the Code

In this section, we will guides you through the process of getting the codebase
of the Event Provenance Registry (EPR) project.

## Clone the Code

Use the following command to clone the EPR project repository:

```bash
git clone git@github.com:sassoftware/event-provenance-registry.git
```

Change into the EPR project directory:

```bash
cd event-provenance-registry
```

## Start Event Provenance Registry server

Export the environment variables for the server

```bash
export EPR_TOPIC=epr.dev.events
export EPR_BROKERS=localhost:19092
export EPR_DB=postgres://localhost:5432
```

The server can be started using the default settings. This will make the server
available on localhost:8042.

```bash
go run main.go
```

We can stop the server using `CTRL + C`.

Later we will build the server binary with `make`.

## Access graphql playground

On successful startup the server will display the message below:

```json
{
  "level": "info",
  "module": "cmd.root",
  "v": 0,
  "logger": "server",
  "timestamp": "2023-07-29T13:56:22.378783-04:00",
  "message": "connect to http://localhost:8042/api/v1/graphql for GraphQL playground"
}
```

The graphql playground will now be accessible at:
<http://localhost:8042/api/v1/graphql>

## Build the server

We are now ready to build the server and install it in our `GOPATH`.

To install in your go path directory set `PREFIX` to your go path. For example,
if you want to install in `~/go/bin` set `PREFIX=~/go`.

Linux

```bash
make PREFIX=$(go env GOPATH) install
```

Mac OS X M1

```bash
make PREFIX=$(go env GOPATH) install-darwin-arm64
```

We can now run the server with the following command:

```bash
epr-server
```
