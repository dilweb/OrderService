import asyncio
import json
import logging

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from orderservice.kafka.config import kafka_settings

logger = logging.getLogger(__name__)


class OrderKafkaProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            client_id="order-service-producer",
            enable_idempotence=True,
            acks="all",
            linger_ms=5,
        )
        self._topic = topic
        self._started = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._started:
                return
            await self._producer.start()
            self._started = True
            logger.info("Kafka producer started")

    async def stop(self) -> None:
        async with self._lock:
            if not self._started:
                return
            await self._producer.stop()
            self._started = False
            logger.info("Kafka producer stopped")

    async def publish_event(self, event: dict) -> bool:
        if not self._started:
            raise RuntimeError("Kafka producer is not started")
        try:
            await self._producer.send_and_wait(
                topic=self._topic,
                key=event["order_id"].encode("utf-8"),
                value=json.dumps(event, ensure_ascii=False).encode("utf-8"),
            )
            logger.debug("order_id=%s message_id=%s published", event.get("order_id"), event.get("message_id"))
            return True
        except KafkaError:
            logger.exception("Kafka publish failed for order %s", event.get("order_id"))
            return False
        except Exception:
            logger.exception("Unexpected error while publishing order %s", event.get("order_id"))
            return False


_order_producer: OrderKafkaProducer | None = None


def get_producer() -> OrderKafkaProducer:
    global _order_producer
    if _order_producer is None:
        _order_producer = OrderKafkaProducer(
            bootstrap_servers=kafka_settings.bootstrap_servers,
            topic=kafka_settings.orders_topic,
        )
    return _order_producer
