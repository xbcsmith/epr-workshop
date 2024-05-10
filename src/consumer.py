import os
from kafka import KafkaConsumer

brokers = os.environ.get("EPR_BROKERS", "localhost:9092")
topic = os.environ.get("EPR_TOPIC", "epr.dev.events")


consumer = KafkaConsumer(
    bootstrap_servers=[brokers],
    group_id="epr-python-consumer",
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    consumer_timeout_ms=1000,
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
