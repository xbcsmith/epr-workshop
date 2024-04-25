# EPR Python Client

## Overview

In this section we will cover the EPR Python Client and how to use it.

## Model Example

A model example using the models in the `epr` package.

```python
from epr.models import Event_Receiver

event_receiver_foo = Event_Receiver()
event_receiver_foo.name = "foo-receiver"
event_receiver_foo.type = "dev.events.foo"
event_receiver_foo.version = "1.0.0"
event_receiver_foo.description = "The Event Receiver for the Foo of Brixton"
event_receiver_foo.schema = "{}"

print(f"Name: {event_receiver_foo.name}")
print(f"Type: {event_receiver_foo.type}")
print(f"Fingerprint: {event_receiver_foo.compute_fingerprint()}")
```

A model example a dictionary and the models in the `epr` package.

```python
from epr.models import Event_Receiver

erf = dict(name="foo-receiver", type="dev.events.foo", version="1.0.0", description="The Event Receiver for the Foo of Brixton", schema="{}")

erf_obj = Event_Receiver(**erf)

print(f"Name: {erf_obj.name}")
print(f"Type: {erf_obj.type}")
print(f"Fingerprint: {erf_obj.compute_fingerprint()}")
```

## Client Example

A Client example using the models in the `epr` package.

```python
from epr.client import Client
from epr.models import Event, Event_Receiver, Event_Receiver_Group

url = "http://localhost:8042"
headers = {}
client = Client(url, headers=headers)

# Create an event receiver
event_receiver_foo = Event_Receiver()
event_receiver_foo.name = "foo-receiver-2"
event_receiver_foo.type = "dev.events.foo"
event_receiver_foo.version = "1.0.0"
event_receiver_foo.description = "The Event Receiver for the Foo of Brixton"
event_receiver_foo.schema = "{}"

event_receiver_foo_res = client.create_event_receiver(params=event_receiver_foo)
event_receiver_foo_id = event_receiver_foo_res["data"]["create_event_receiver"]


event_receiver_bar = Event_Receiver()
event_receiver_bar.name = "bar-receiver-1"
event_receiver_bar.type = "dev.events.bar"
event_receiver_bar.version = "1.0.0"
event_receiver_bar.description = "The Event Receiver for the Bar of Brixton"
event_receiver_bar.schema = "{}"

event_receiver_bar_res = client.create_event_receiver(params=event_receiver_bar)
event_receiver_bar_id = event_receiver_bar_res["data"]["create_event_receiver"]

# Create an event receiver group

event_receiver_group_foo = Event_Receiver_Group()
event_receiver_group_foo.name = "foo-bar-receiver-group-1"
event_receiver_group_foo.type = "dev.events.foo.bar.complete"
event_receiver_group_foo.version = "1.0.0"
event_receiver_group_foo.description = "The Event Receiver Group for the Foo and Bar of Brixton"
event_receiver_group_foo.event_receiver_ids = [event_receiver_foo_id, event_receiver_bar_id]

event_receiver_group_foo_res = client.create_event_receiver_group(params=event_receiver_group_foo)
event_receiver_group_foo_id = event_receiver_group_foo_res["data"]["create_event_receiver_group"]

# Create an event

event_foo = Event()
event_foo.name = "foo"
event_foo.version = "1.0.0"
event_foo.release = str(time.time())
event_foo.platform_id = "x86_64-gnu-linux-9"
event_foo.package = "rpm"
event_foo.description = "The Foo of Brixton"
event_foo.payload = "{\"name\": \"foo\"}"
event_foo.success = True
event_foo.event_receiver_id = event_receiver_foo_id

event_foo_res = client.create_event(params=event_foo)
event_foo_id = event_foo_res["data"]["create_event"]

event_bar = Event()
event_bar.name = "bar"
event_bar.version = "1.0.0"
event_bar.release = str(time.time())
event_bar.platform_id = "x86_64-gnu-linux-9"
event_bar.package = "rpm"
event_bar.description = "The Bar of Brixton"
event_bar.payload = "{\"name\": \"bar\"}"
event_bar.success = True
event_bar.event_receiver_id = event_receiver_bar_id

event_bar_res = client.create_event(params=event_bar)
event_bar_id = event_bar_res["data"]["create_event"]

results = {"events": [event_foo_id, event_bar_id], "event_receivers": [event_receiver_foo_id, event_receiver_bar_id], "event_receiver_groups": [event_receiver_group_foo_id]}

print(f"{results}")
```

### TL;DR Client Example

Create an event receiver and event receiver group. Then send events.

```python
from epr.client import Client
from epr.models import Event, Event_Receiver, Event_Receiver_Group

url = "http://localhost:8042"
headers = {}
client = Client(url, headers=headers)

erf = dict(name="foo-receiver-3", type="dev.events.foo", version="1.0.0", description="The Event Receiver for the Foo of Brixton", schema="{}")

erf_res = client.create_event_receiver(params=erf)
erf_id = erf_res["data"]["create_event_receiver"]


erb = dict(name="bar-receiver-4", type="dev.events.bar", version="1.0.0", description="The Event Receiver for the Bar of Brixton", schema="{}")

erb_res = client.create_event_receiver(params=erb)
erb_id = erb_res["data"]["create_event_receiver"]

erg = dict(name="foo-bar-receiver-group-2", type="dev.events.foo.bar.complete", version="1.0.0", description="The Event Receiver Group for the Foo and Bar of Brixton", event_receiver_ids=[erf_id, erb_id])

erg_res = client.create_event_receiver_group(params=erg)
erg_id = erg_res["data"]["create_event_receiver_group"]

ef = dict(name="foo", version="1.0.0", release=str(time.time()), platform_id="x86_64-gnu-linux-9", package="rpm", description="The Foo of Brixton", payload="{}", success=True, event_receiver_id=erf_id)

ef_res = client.create_event(params=ef)
ef_id = ef_res["data"]["create_event"]

eb = dict(name="bar", version="1.0.0", release=str(time.time()), platform_id="x86_64-gnu-linux-9", package="rpm", description="The Bar of Brixton", payload="{}", success=True, event_receiver_id=erb_id)

eb_res = client.create_event(params=eb)
eb_id = eb_res["data"]["create_event"]

results = {"events": [ef_id, eb_id], "event_receivers": [erf_id, erb_id], "event_receiver_groups": [erg_id]}
print(f"{results}")
```
