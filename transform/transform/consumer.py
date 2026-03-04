import json
from typing import Iterator

import structlog
from confluent_kafka import Consumer, KafkaError

logger = structlog.get_logger()


class KafkaConsumer:
    """Wraps confluent_kafka.Consumer with JSON deserialisation."""

    def __init__(self, brokers: str, group_id: str, topic: str) -> None:
        self._consumer = Consumer(
            {
                "bootstrap.servers": brokers,
                "group.id": group_id,
                "auto.offset.reset": "latest",
                "enable.auto.commit": True,
            }
        )
        self._topic = topic
        self._consumer.subscribe([topic])
        logger.info("kafka_consumer_subscribed", topic=topic, group_id=group_id)

    def events(self, timeout: float = 1.0) -> Iterator[dict]:
        """Yield parsed event dicts from Kafka indefinitely."""
        while True:
            msg = self._consumer.poll(timeout)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("kafka_consumer_error", error=str(msg.error()))
                continue

            try:
                event = json.loads(msg.value().decode("utf-8"))
                yield event
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.warning("event_parse_failed", error=str(exc))

    def close(self) -> None:
        self._consumer.close()
