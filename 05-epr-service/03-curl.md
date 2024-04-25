# Curl

In this section of the workshop we will use curl to make requests to the Event
Provenance Registry.

## Create using the REST API

First thing we need is an event receiver. The event receiver acts as a
classification and gate for events.

Create an event receiver:

```bash
curl --location --request POST 'http://localhost:8042/api/v1/receivers' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "foobar",
    "type": "foo.bar",
    "version": "1.1.3",
    "description": "The event receiver of Brixton",
    "enabled": true,
    "schema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string"
      }
    }
  }
}'
```

The results should look like this:

```json
{ "data": "01HPW0DY340VMM3DNMX8JCQDGN" }
```

We need the ULID of the event receiver in the next step.

Create an event using curl.

When you create an event, you must specify an `event_receiver_id` to associate
it with. An event is the record of some action being completed. You cannot
create an event for a non-existent receiver ID. The payload field of the event
must conform to the schema defined on the event receiver that you have given the
ID of.

Create an event:

```bash
curl --location --request POST 'http://localhost:8042/api/v1/events' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "magnificent",
    "version": "7.0.1",
    "release": "2023.11.16",
    "platform_id": "linux",
    "package": "docker",
    "description": "blah",
    "payload": {"name":"joe"},
    "success": true,
    "event_receiver_id": "<PASTE EVENT RECEIVER ID FROM FIRST CURL COMMAND>"
}'
```

The results of the command should look like this:

```json
{ "data": "01HPW0GV9PY8HT2Q0XW1QMRBY9" }
```

Event Receiver Groups are a way to group together several event receivers. When
all the event receivers in a group have successful events for a given unit the
event receiver group will produce a message on the topic.

Create an event receiver group:

```bash
curl --location --request POST 'http://localhost:8042/api/v1/groups' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "the_clash",
    "type": "foo.bar",
    "version": "3.3.3",
    "description": "The only event receiver group that matters",
    "enabled": true,
    "event_receiver_ids": ["PASTE EVENT RECEIVER ID FROM FIRST CURL COMMAND"]
}'
```

## Query using the REST API

We can query the event information using a GET on the events endpoint as
follows:

```bash
curl --header 'Content-Type: application/json' --location \
  --request GET 'http://localhost:8042/api/v1/events/01HPW0GV9PY8HT2Q0XW1QMRBY9'
```

Query the information for an event receiver:

```bash
curl --header 'Content-Type: application/json' --location \
  --request GET 'http://localhost:8042/api/v1/receivers/01HPW0DY340VMM3DNMX8JCQDGN'
```

And query the information for an event receiver group:

```bash
curl --header 'Content-Type: application/json' --location \
  --request GET 'http://localhost:8042/api/v1/groups/01HPW0JXG82Q0FBEC9M8P2Q6J8
'
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

Create an event receiver group using the GraphQL with Curl #TODO FIXME

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"mutation ($obj: CreateEventReceiverGroupInput!){create_event_receiver_group(event_receiver_group: $obj)}", "variables": {"obj": {"name": "foo", "version": "1.0.0"}}}' http://localhost:8042/api/v1/graphql/query
```

Create an event using the GraphQL with Curl #TODO FIXME

```bash
curl -X POST -H "content-type:application/json" -d '{"query":"mutation ($obj: CreateEventInput!){create_event(event: $obj)}", "variables": {"obj": {"name": "foo", "version": "1.0.0"}}}' http://localhost:8042/api/v1/graphql/query
```
