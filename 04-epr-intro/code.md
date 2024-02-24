# Get the Code

Initiate the workshop by guiding participants on how to clone and get the codebase of the Event Provenance Registry (EPR) project.

## Clone the Code

```bash
git clone git@github.com:sassoftware/event-provenance-registry.git
```

## Repository Structure

The codebase is structured as follows:

Event Provenance Registry (EPR) Server Packages

```bash
├── cmd
│   └── root.go
├── docker-compose.services.yaml
├── docker-compose.yaml
├── docs
│   ├── README.md
│   ├── explanations
│   │   ├── README.md
│   │   ├── arch
│   │   │   ├── DECISIONS.md
│   │   │   ├── README.md
│   │   │   └── adr-1-use-adrs.md
│   │   ├── cdf-blog.md
│   │   └── enhancements
│   │       ├── README.md
│   │       └── REP-1.md
│   ├── how-to
│   │   ├── README.md
│   │   ├── redpanda
│   │   │   ├── README.md
│   │   │   ├── multi-node
│   │   │   │   ├── docker-compose.yaml
│   │   │   │   └── redpanda_deploy.md
│   │   │   └── single-node
│   │   │       └── README.md
│   │   ├── start-server
│   │   │   └── README.md
│   │   └── watcher
│   │       ├── README.md
│   │       ├── go.mod
│   │       ├── go.sum
│   │       └── main.go
│   ├── reference
│   │   ├── README.md
│   │   └── glossary.md
│   └── tutorials
│       ├── README.md
│       ├── cdevents
│       │   └── README.md
│       ├── hello_world
│       │   └── README.md
│       ├── sboms
│       │   └── README.md
│       └── watcher
│           └── README.md
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
│   │   │           ├── event_reciever.graphql
│   │   │           ├── event_reciever_group.graphql
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
    ├── README.md
    ├── common
    │   └── net.go
    ├── e2e
    │   ├── api_event.go
    │   ├── api_event_receiver.go
    │   ├── api_event_receiver_group.go
    │   ├── api_event_receiver_group_test.go
    │   ├── api_event_receiver_test.go
    │   └── api_event_test.go
    ├── go.mod
    └── go.sum
```

Event Provenance Registry (EPR) CLI

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
│   │   ├── README.md
│   │   ├── explanations
│   │   │   ├── README.md
│   │   │   ├── arch
│   │   │   │   ├── DECISIONS.md
│   │   │   │   ├── README.md
│   │   │   │   └── adr-1-use-adrs.md
│   │   │   └── enhancements
│   │   │       ├── README.md
│   │   │       └── REP-1.md
│   │   ├── how-to
│   │   │   └── README.md
│   │   ├── reference
│   │   │   └── README.md
│   │   └── tutorials
│   │       ├── README.md
│   │       └── hello_world.md
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   ├── temp
│   │   └── README.md
│   └── testdata
│       ├── e_bar.json
│       ├── e_foo.json
│       ├── er_bar.json
│       ├── er_foo.json
│       ├── erg_foo.json
│       └── list_er.json
```