# GraphQL Playground

The GraphQL Playground is a tool that allows you to test your GraphQL queries in
a browser.

The graphql playground will now be accessible at:

[http://localhost:8042/api/v1/graphql](http://localhost:8042/api/v1/graphql)

## Making a request

The current schema for all requests is available through the UI. Mutations are
create events in GraphQL. Querys are read events in GraphQL. A simple mutation
and query commands can be found below.

## Mutation using GraphQL

To start, we will need to create an event receiver.

Create an event receiver by pasting the following mutation into the GraphQL
Playground.

```graphql
mutation {
  create_event_receiver(
    event_receiver: {
      name: "the_clash"
      version: "1.0.0"
      type: "london.calling"
      description: "The only band that matters"
      schema: "{\"name\": \"value\"}"
    }
  )
}
```

This will return the id of the newly created event receiver. Save this ID off to
the side. We will need it later in the workshop to create events and event
receiver groups.

```json
{
  "data": {
    "create_event_receiver": "01HPVZY1V8SVXGQY03ZG90CA3S"
  }
}
```

This can then be used to create a new event receiver group

```graphql
mutation {
  create_event_receiver_group(
    event_receiver_group: {
      name: "foobar"
      version: "1.0.0"
      description: "a fake event receiver group"
      enabled: true
      event_receiver_ids: ["ID_RETURNED_FROM_PREVIOUS_MUTATION"]
      type: "test.test.test"
    }
  )
}
```

This will return the id of the newly created event receiver group.

```json
{
  "data": {
    "create_event_receiver_group": "01HPW02R3G3QP3EJB036M41J9J"
  }
}
```

Event receiver Groups can be updated using the following mutation

```graphql
mutation {
  set_event_receiver_group_enabled(id: "01HPW02R3G3QP3EJB036M41J9J")
}
```

```graphql
mutation {
  set_event_receiver_group_disabled(id: "01HPW02R3G3QP3EJB036M41J9J")
}
```

Now can create a new event for the event receiver ID in the previous step

```graphql
mutation {
  create_event(
    event: {
      name: "foo"
      version: "1.0.0"
      release: "20231103"
      platform_id: "platformID"
      package: "package"
      description: "The Foo of Brixton"
      payload: "{\"name\": \"value\"}"
      event_receiver_id: "ID_RETURNED_FROM_PREVIOUS_MUTATION"
      success: true
    }
  )
}
```

This will return the id of the newly created event.

```json
{
  "data": {
    "create_event": "01HPW06R5QXK0C2GZM8H442Q9F"
  }
}
```

## Query using GraphQL

This query is only returning a subset of the available fields. Pass in the ID of
the previously created event

```graphql
query {
  events_by_id(id: "01K61C8NEDP8SDS7HVMFZ69CEF") {
    id
    name
    version
    release
    platform_id
    package
    description
    payload
    success
    event_receiver_id
    created_at
  }
}
```

This query is only returning a subset of the available fields. Pass in the ID of
the previously created event_receiver

```graphql
query {
  event_receivers_by_id(id: "01HPVZY1V8SVXGQY03ZG90CA3S") {
    name
    version
    description
    type
    schema
    fingerprint
    created_at
  }
}
```

This query is only returning a subset of the available fields. Pass in the ID of
the previously created event_receiver_group

```graphql
query {
  event_receiver_groups_by_id(id: "01HPW02R3G3QP3EJB036M41J9J") {
    name
    version
    description
    type
    enabled
    event_receiver_ids
    created_at
    updated_at
  }
}
```

We can use graphql to search for events by name and version.

Create another event for the same event receiver

```graphql
mutation {
  create_event(
    event: {
      name: "foo"
      version: "1.0.0"
      release: "20240217"
      platform_id: "x86-64-gnu-linux-7"
      package: "rpm"
      description: "The RPM Foo of Brixton"
      payload: "{\"name\": \"foo\"}"
      event_receiver_id: "01HPVZY1V8SVXGQY03ZG90CA3S"
      success: true
    }
  )
}
```

In the graphql window create a query with the following:

```graphql
query {
  events(event: { name: "foo", version: "1.0.0" }) {
    id
    name
    version
    release
    platform_id
    package
    description
    payload
    success
    event_receiver_id
    created_at
  }
}
```

This query will return all events with the name foo and version 1.0.0

As follows:

```json
{
  "data": {
    "events": [
      {
        "id": "01HPW06R5QXK0C2GZM8H442Q9F",
        "name": "foo",
        "version": "1.0.0",
        "release": "20231103",
        "platform_id": "platformID",
        "package": "package",
        "description": "The Foo of Brixton",
        "payload": {
          "name": "value"
        },
        "success": true,
        "event_receiver_id": "01HPVZY1V8SVXGQY03ZG90CA3S",
        "created_at": "2024-02-17T12:00:45.62347-05:00"
      },
      {
        "id": "01HPW1WMPK0ZDHQYD6T40MZBGW",
        "name": "foo",
        "version": "1.0.0",
        "release": "20240217",
        "platform_id": "x86-64-gnu-linux-7",
        "package": "rpm",
        "description": "The RPM Foo of Brixton",
        "payload": {
          "name": "foo"
        },
        "success": true,
        "event_receiver_id": "01HPVZY1V8SVXGQY03ZG90CA3S",
        "created_at": "2024-02-17T12:30:11.539643-05:00"
      }
    ]
  }
}
```

We can use graphql to search for event receivers by name and version.

Create another event receiver

```graphql
mutation {
  create_event_receiver(
    event_receiver: {
      name: "the_clash"
      version: "1.0.0"
      type: "london.calling.from.the.far.away.town"
      description: "The only band that matters"
      schema: "{\"name\": \"joe\"}"
    }
  )
}
```

In the graphql window create a query with the following:

```graphql
query {
  event_receivers(event_receiver: { name: "the_clash", version: "1.0.0" }) {
    id
    name
    version
    type
    description
    created_at
  }
}
```

This query will return all events with the name the_clash and version 1.0.0

As follows:

```graphql
{
  "data": {
    "event_receivers": [
      {
        "id": "01HPVZY1V8SVXGQY03ZG90CA3S",
        "name": "the_clash",
        "version": "1.0.0",
        "type": "london.calling",
        "description": "The only band that matters",
        "created_at": "2024-02-17T11:56:00.616222-05:00"
      },
      {
        "id": "01HPW2BBY8HGPS6JG10DCXE6EH",
        "name": "the_clash",
        "version": "1.0.0",
        "type": "london.calling.from.the.far.away.town",
        "description": "The only band that matters",
        "created_at": "2024-02-17T12:38:14.088635-05:00"
      }
    ]
  }
}
```

## Query using the GraphQL with Curl

We need to craft a GraphQL query. First thing we need is an event receiver. The
event receiver acts as a classification and gate for events.

We can find and event receiver by id using the following graphql query:

```json
{
  "query": "query ($er: FindEventReceiverInput!){event_receivers(event_receiver: $er) {id,name,type,version,description}}",
  "variables": {
    "er": {
      "id": "01HPW652DSJBHR5K4KCZQ97GJP"
    }
  }
}
```

We can query the event receiver information using a POST on the graphql endpoint
as follows:

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"query ($er: FindEventReceiverInput!){event_receivers(event_receiver: $er) {id,name,type,version,description}}","variables":{"er":{"id":"01HPW652DSJBHR5K4KCZQ97GJP"}}}' http://localhost:8042/api/v1/graphql/query
```

We can query for an event by name and version using the following graphql query:

```json
{
  "query": "query ($e: FindEventInput!){events(event: $e) {id,name,version,release,platform_id,package,description,success,event_receiver_id}}",
  "variables": {
    "e": {
      "name": "foo",
      "version": "1.0.0"
    }
  }
}
```

We can query the event receiver information using a POST on the graphql endpoint
as follows:

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"query ($e : FindEventInput!){events(event: $e) {id,name,version,release,platform_id,package,description,success,event_receiver_id}}","variables":{"e": {"name":"foo","version":"1.0.0"}}}' http://localhost:8042/api/v1/graphql/query
```

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"query {events(event: {name: \"foo\", version: \"1.0.0\"}) {id,name,version,release,platform_id,package,description,success,event_receiver_id}}}' http://localhost:8042/api/v1/graphql/query
```

We can query for an event receiver group by name and version using the following
graphql query:

```json
{
  "query": "query ($erg: FindEventReceiverGroupInput!){event_receiver_groups(event_receiver_group: $erg) {id,name,type,version,description}}",
  "variables": {
    "erg": {
      "name": "foobar",
      "version": "1.0.0"
    }
  }
}
```

We can query the event receiver information using a POST on the graphql endpoint
as follows:

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"query ($erg: FindEventReceiverGroupInput!){event_receiver_groups(event_receiver_group: $erg) {id,name,type,version,description}}","variables":{"erg": {"name":"foobar","version":"1.0.0"}}}' http://localhost:8042/api/v1/graphql/query
```

### Create using GraphQL with Curl

We can create an event receiver using the following graphql query:

```json
{
  "query": "mutation ($er: CreateEventReceiverInput!){create_event_receiver(event_receiver: $er)}",
  "variables": {
    "er": {
      "name": "foobar",
      "version": "1.3.0",
      "description": "foobar is the description",
      "type": "foobar.test",
      "schema": "{}"
    }
  }
}
```

We can create the event receiver using a POST on the graphql endpoint as
follows:

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"mutation ($er: CreateEventReceiverInput!){create_event_receiver(event_receiver: $er)}","variables":{"er": {"name":"foobar","version":"1.3.0","description":"foobar is the description","type": "foobar.test", "schema" : "{}"}}}' http://localhost:8042/api/v1/graphql/query
```

We will need the event receiver ID returned from this mutation in the next step.

```json
{
  "data": {
    "create_event_receiver": "01HXS65KV33MP0PSW98P82WKR6"
  }
}
```

Create an event receiver group using the GraphQL with Curl. You will need the
Event Receiver ID returned from the previous mutation.

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"mutation ($obj: CreateEventReceiverGroupInput!){create_event_receiver_group(event_receiver_group: $obj)}", "variables": {"obj": {"name": "foobar", "version": "1.0.0", "type": "test.test.test", "description": "a fake event receiver group", "enabled": true, "event_receiver_ids": ["<ID_RETURNED_FROM_EVENT_RECEIVER_MUTATION>"]}}}' http://localhost:8042/api/v1/graphql/query
```

```json
{
  "data": {
    "create_event_receiver_group": "01HXS6K78PYDRTMVQCRS4FF2VS"
  }
}
```

Create an event using the GraphQL with Curl. You will need the Event Receiver ID
returned from the previous mutation.

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"mutation ($obj: CreateEventInput!){create_event(event: $obj)}", "variables": {"obj": {"name": "foo", "version": "1.0.0", "release": "2023.11.16", "platform_id": "linux", "package": "docker", "description": "blah", "payload": "{\"name\":\"joe\"}", "success": true, "event_receiver_id": "<ID_RETURNED_FROM_EVENT_RECEIVER_MUTATION>"}}}' http://localhost:8042/api/v1/graphql/query
```

```json
{
  "data": {
    "create_event": "01HXS6RHE2M48RQBZ97Q8YNG49"
  }
}
```
