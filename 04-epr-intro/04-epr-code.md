# EPR Codebase

Begin your exploration of the Event Provenance Registry (EPR) project by gaining
access to the codebase and understanding its structure.

## Clone the Code

Use the following command to clone the EPR project repository:

```bash
git clone git@github.com:sassoftware/event-provenance-registry.git
```

## Repository Structure

Let's take a look at the repository structure. Currently, the EPR project is
layed out like an SDK.

The codebase is structured as follows:

### Event Provenance Registry (EPR) Server Packages

```bash
├── cmd
│   └── root.go
├── docker-compose.services.yaml
├── docker-compose.yaml
├── docs
├── gencerts.sh
├── go.mod
├── go.sum
├── golangci-megalint-config.yaml
├── main.go
├── pkg
│   ├── api
│   │   ├── api.go
│   │   ├── graphql
│   │   │   ├── graphql.go
│   │   │   ├── resolvers
│   │   │   │   ├── models.go
│   │   │   │   ├── mutations.go
│   │   │   │   ├── query.go
│   │   │   │   └── resolver.go
│   │   │   ├── resources
│   │   │   │   └── graphql.html
│   │   │   └── schema
│   │   │       ├── schema.go
│   │   │       ├── schema.graphql
│   │   │       ├── schema_test.go
│   │   │       └── types
│   │   │           ├── event.graphql
│   │   │           ├── event_receiver.graphql
│   │   │           ├── event_receiver_group.graphql
│   │   │           ├── json.go
│   │   │           ├── json.graphql
│   │   │           ├── time.go
│   │   │           ├── time.graphql
│   │   │           └── time_test.go
│   │   ├── middleware.go
│   │   ├── rest
│   │   │   ├── event.go
│   │   │   ├── group.go
│   │   │   ├── receiver.go
│   │   │   └── rest.go
│   │   ├── server.go
│   │   └── status.go
│   ├── auth
│   │   └── auth.go
│   ├── client
│   │   ├── check.go
│   │   ├── client.go
│   │   ├── client_test.go
│   │   ├── constants.go
│   │   ├── create.go
│   │   ├── graphql.go
│   │   ├── graphql_test.go
│   │   ├── response_test.go
│   │   ├── responses.go
│   │   └── search.go
│   ├── config
│   │   ├── config.go
│   │   └── config_test.go
│   ├── errors
│   │   └── errors.go
│   ├── message
│   │   ├── constants.go
│   │   ├── consume.go
│   │   ├── message.go
│   │   ├── message_test.go
│   │   ├── produce.go
│   │   ├── sasl.go
│   │   ├── sasl_test.go
│   │   └── scram.go
│   ├── metrics
│   │   └── metrics.go
│   ├── status
│   │   ├── status.go
│   │   ├── status_test.go
│   │   ├── version.go
│   │   └── version_test.go
│   ├── storage
│   │   ├── db.go
│   │   ├── megaQuery.sql
│   │   ├── schema.go
│   │   ├── schema_test.go
│   │   └── setup-db.sql
│   ├── utils
│   │   ├── utils.go
│   │   └── utils_test.go
│   └── watcher
│       └── watcher.go
└── tests
```

### Event Provenance Registry (EPR) CLI

```bash
├── cli
│   ├── Makefile
│   ├── README.md
│   ├── bin
│   │   └── epr-cli-darwin
│   ├── cmd
│   │   ├── common
│   │   │   ├── common.go
│   │   │   └── common_test.go
│   │   ├── event
│   │   │   ├── create.go
│   │   │   ├── event.go
│   │   │   ├── generate.go
│   │   │   └── search.go
│   │   ├── group
│   │   │   ├── create.go
│   │   │   ├── generate.go
│   │   │   ├── group.go
│   │   │   ├── modify.go
│   │   │   └── search.go
│   │   ├── receiver
│   │   │   ├── create.go
│   │   │   ├── generate.go
│   │   │   ├── receiver.go
│   │   │   └── search.go
│   │   ├── root.go
│   │   └── status
│   │       └── status.go
│   ├── docs
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   └── testdata
```

## Develop

EPR provides a `Makefile` which can be used to build and install the project.

### Build

Build the server binaries for several platforms.

```bash
make
```

## Installation

Install the server binaries in the `bin` directory.

The default install location is `/usr/local/bin`. You can install in the
`/usr/local/bin` directory by running the following command:

Linux

```bash
make install
```

Mac OS X

```bash
make install-darwin
```

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

## Tests

Run the go unit tests:

```bash
make test
```

## Linter

Run golangci-lint (requires
[golangci-lint](https://golangci-lint.run/usage/install/) to be installed):

```bash
make lint
```

## Usage

The `epr-server` command is used to start the EPR server.

```txt
Usage:
  epr-server [flags]

Flags:
      --brokers string   broker uris separated by commas (default "localhost:9092")
      --config string    config file (default is $XDG_CONFIG_HOME/epr/epr.yaml)
      --db string        database connection string (default "postgres://localhost:5432")
      --debug            Enable debugging statements
  -h, --help             help for epr-server
      --host string      host to listen on (default "localhost")
      --port string      port to listen on (default "8042")
      --topic string     topic to produce events on (default "epr.dev.events")
```
