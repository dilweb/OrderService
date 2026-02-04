import logging
import os

from pydantic_settings import BaseSettings


class KafkaSettings(BaseSettings):
    bootstrap_servers: str = "localhost:9092"
    orders_topic: str = "order.events"
    orders_consumer_group: str = "order-service-notifier"

    class Config:
        env_prefix = "KAFKA_"


logger = logging.getLogger(__name__)
kafka_settings = KafkaSettings()
logger.debug(
    "KafkaSettings initialized (bootstrap=%s, topic=%s, group=%s, env=%s)",
    kafka_settings.bootstrap_servers,
    kafka_settings.orders_topic,
    kafka_settings.orders_consumer_group,
    os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
)
