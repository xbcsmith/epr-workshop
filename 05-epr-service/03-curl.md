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
  "payload": {
    "name": "joe"
  },
  "success": true,
  "event_receiver_id": "<PASTE EVENT RECEIVER ID FROM FIRST CURL COMMAND>"
}
```

curl --location --request POST 'http://localhost:8042/api/v1/events' \
--header 'Content-Type: application/json' \
--data-raw '{
  "name": "magnificent",
  "version": "7.0.1",
  "release": "2023.11.16",
  "platform_id": "linux",
  "package": "docker",
  "description": "blah",
  "payload": {
    "name": "joe"
  },
  "success": true,
  "event_receiver_id": "01K61BP7CRT5YXQW6SAJK91H5C"
}


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
  "event_receiver_ids": [
    "PASTE EVENT RECEIVER ID FROM FIRST CURL COMMAND"
  ]
}
```

Note: You can extract the event receiver id from the previous command by pipe
the output to `| jq .data`

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
