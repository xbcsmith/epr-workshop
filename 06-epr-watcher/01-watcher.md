# Watcher

## Overview

In this section we will delve into the utilization of the EPR watcher SDK to
craft a watcher, which actively listens for events originating from the EPR
server. Watchers serve the purpose of monitoring messages within Redpanda,
initiating actions based on these messages, and subsequently dispatching event
notifications to the EPR Server.

---

## Requirements

The [Quickstart](../quickstart/README.md) has been completed and the EPR server
is running.

---

## Create a new watcher

Make a new directory for your watcher and create a `main.go` in that directory.

```bash
mkdir -p ./src/foo
cd ./src/foo
touch main.go
```

---

Now open the `main.go` in your favorite editor (Vim).

Add the following code:

```go
package main

import (
 "log"

 "github.com/sassoftware/event-provenance-registry/pkg/message"
 "github.com/sassoftware/event-provenance-registry/pkg/watcher"
)

func main() {
 seeds := []string{"localhost:19092"}
 topics := []string{"epr.dev.events"}
 consumerGroup := "watcher-workshop"

 watcher, err := watcher.New(seeds, topics, consumerGroup)
 if err != nil {
  panic(err)
 }
 defer watcher.Client.Close()

 go watcher.StartTaskHandler(customTaskHandler)

 watcher.ConsumeRecords(customMatcher)
}

func customMatcher(msg *message.Message) bool {
 return msg.Type == "foo.bar"
}

func customTaskHandler(msg *message.Message) error {
 log.Default().Printf("I received a task with value '%v'", msg)
 return nil
}

```

---

Save the file and run `go mod init` in your terminal.

```bash
go mod init
```

Now we can run `go mod tidy` to fill in our dependencies.

```bash
go mod tidy
```

---

## Begin consuming

We can now start up the watcher and start consuming messages.

```bash
go run main.go
```

You should see a log stating that we have begin consuming records.

---

## Create an event receiver

Time to create an event receiver.

In a second terminal run the command below:

```bash
curl --location --request POST 'http://localhost:8042/api/v1/receivers' \
--header 'Content-Type: application/json' \
--data-raw '{
  "name": "watcher-workshop",
  "type": "foo.bar",
  "version": "1.0.0",
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

---

## Produce message

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
    "event_receiver_id": "01K61CMNCCT3B5CH95YHJDXZ15"
}'
```

---

## Receive message

You should now see a message like the one below.

```bash
2023/11/17 16:18:30 I received a task with value '{"success":true,"id":"01HFFJCJYZN02RR1JSCE9DDAS4","specversion":"1.0","type":"foo.bar","source":"","api_version":"v1","name":"magnificent","version":"7.0.1","release":"2023.11.16","platform_id":"linux","package":"docker","data":{"events":[{"id":"01HFFJCJYZN02RR1JSCE9DDAS4","name":"magnificent","version":"7.0.1","release":"2023.11.16","platform_id":"linux","package":"docker","description":"blah","payload":{"name":"joe"},"success":true,"created_at":"16:18:30.000879894","event_receiver_id":"01HFFJ69HHJ506SRDYQMFF1H5A","EventReceiver":{"id":"01HFFJ69HHJ506SRDYQMFF1H5A","name":"watcher-workshop","type":"foo.bar","version":"1.0.0","description":"The event receiver of Brixton","schema":{"type":"object","properties":{"name":{"type":"string"}}},"fingerprint":"b183c34c7ba56b17f89dfe0c0b22c0a340889cae88d8e87a3f16bc5bdc8f7acb","created_at":"16:15:04.000626147"}}],"event_receivers":[{"id":"01HFFJ69HHJ506SRDYQMFF1H5A","name":"watcher-workshop","type":"foo.bar","version":"1.0.0","description":"The event receiver of Brixton","schema":{"type":"object","properties":{"name":{"type":"string"}}},"fingerprint":"b183c34c7ba56b17f89dfe0c0b22c0a340889cae88d8e87a3f16bc5bdc8f7acb","created_at":"16:15:04.000626147"}],"event_receiver_groups":null}}
```

**Note**: the matcher being run is looking for kafka messages with the type
`foo.bar`. This aligns with the type of the event receiver we created and posted
an event to. All other messages will be ignored.

---
