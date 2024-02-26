# Building EPR Server

In this section we will build the Event Provenance Registry (EPR) server.

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

```txt
time=2024-02-26T09:44:52.943-05:00 level=INFO msg="TLS Not Enabled"
time=2024-02-26T09:44:52.943-05:00 level=INFO msg="connect to http://localhost:8042/api/v1/graphql for GraphQL playground"
```

The graphql playground will now be accessible at:
<http://localhost:8042/api/v1/graphql>

## Install the server

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
