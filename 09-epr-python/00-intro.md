# Intro to EPR Python

## Overview

EPR Python is a python client for the Event Provenance Registry server.

## Development

```bash
python3 -m venv ~/.virtualenvs/epr-python
source ~/.virtualenvs/epr-python/bin/activate

git clone git@github.com:xbcsmith/epr-python.git
cd epr-python

pip install -e .
```

### Development dependencies

```bash
pip install -e .[lint,test,build]
```

## Consumer

First we will write a consumer that will consume messages from the Event
Provenance Registry.

Install the `kafka-python` library.

```bash
python3 pip install --upgrade kafka-python
```

Create the consumer.

```python
import os
from kafka import KafkaConsumer

brokers = os.environ.get("EPR_BROKERS", "localhost:9092")
topic = os.environ.get("EPR_TOPIC", "epr.dev.events")


consumer = KafkaConsumer(
  bootstrap_servers=[brokers],
  group_id="epr-python-consumer",
  auto_offset_reset="earliest",
  enable_auto_commit=False,
  consumer_timeout_ms=1000
)

consumer.subscribe(topic)

try:
    for message in consumer:
        topic_info = f"topic: {message.partition}|{message.offset})"
        message_info = f"key: {message.key}, {message.value}"
        print(f"{topic_info}, {message_info}")
except Exception as e:
    print(f"Error occurred while consuming messages: {e}")
finally:
    consumer.close()
```

In a separate terminal run the following command:

```bash
export EPR_TOPIC=epr.dev.events
export EPR_BROKERS=localhost:19092
```

```bash
python3 consumer.py
```
