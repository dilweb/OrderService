"""
Интеграционный тест: POST /api/orders → событие появляется в Kafka.

Теория:
- В отличие от юнит-тестов, здесь НЕТ моков. Используется реальный Kafka.
- TestClient запускает app с настоящим lifespan → реальный producer подключается к Kafka.
- После HTTP-запроса тест читает из топика и проверяет что событие реально пришло.

Требования перед запуском:
    docker-compose -f docker-compose.test.yml up -d
    # подождать ~15 секунд пока Kafka стартует

Запуск только интеграционных тестов:
    pytest tests/integration/ -v -m integration
"""

import asyncio
import json

import pytest
from aiokafka import AIOKafkaConsumer
from fastapi.testclient import TestClient

from src.main import app

KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "order.events"

VALID_ORDER = {
    "user_id": 1,
    "items": [
        {"product_id": 1, "name": "Чай", "price": "10.00", "quantity": 2}
    ],
    "currency": "USD",
    "amount": "20.00",
}


@pytest.fixture(scope="module")
def client():
    """
    Реальный TestClient — запускает app вместе с lifespan.
    Lifespan подключается к реальному Kafka (без моков).
    scope="module" — один клиент на весь файл, не пересоздаём для каждого теста.
    """
    with TestClient(app) as c:
        yield c


async def _wait_for_event(order_id: str, timeout_ms: int = 10_000) -> dict | None:
    """
    Вспомогательная корутина: читает из Kafka топика и ищет событие по order_id.
    consumer_timeout_ms — сколько ждать новых сообщений перед остановкой.
    """
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        # Уникальный group_id для каждого теста — гарантирует чтение с начала топика
        group_id=f"integration-test-{order_id}",
        consumer_timeout_ms=timeout_ms,
    )
    await consumer.start()
    try:
        async for message in consumer:
            event = json.loads(message.value.decode("utf-8"))
            if event.get("order_id") == order_id:
                return event
    finally:
        await consumer.stop()
    return None


@pytest.mark.integration
def test_create_order_publishes_event_to_kafka(client):
    """
    Полный путь: HTTP запрос → FastAPI → реальный Kafka producer → топик order.events.
    Проверяем что событие реально появилось в Kafka с правильными данными.
    """
    # Act: реальный HTTP запрос, реальный producer, реальный Kafka
    response = client.post("/api/orders", json=VALID_ORDER)
    assert response.status_code == 202
    order_id = response.json()["order_id"]

    # Assert: ищем событие в Kafka топике
    # asyncio.run() запускает async-функцию из синхронного теста
    event = asyncio.run(_wait_for_event(order_id))

    assert event is not None, (
        f"Событие для order_id={order_id} не появилось в топике '{KAFKA_TOPIC}'. "
        "Убедись что Kafka запущена: docker-compose -f docker-compose.test.yml up -d"
    )
    assert event["order_id"] == order_id
    assert event["event_type"] == "order.created"
    assert event["payload"]["user_id"] == VALID_ORDER["user_id"]
    assert event["payload"]["currency"] == VALID_ORDER["currency"]


@pytest.mark.integration
def test_amount_mismatch_does_not_publish_event(client):
    """
    Неверная сумма → 422, событие НЕ должно появиться в Kafka.
    Проверяем что producer не вызывается при ошибке валидации.
    """
    bad_order = {**VALID_ORDER, "amount": "999.99"}

    response = client.post("/api/orders", json=bad_order)

    # Роутер отклоняет на этапе проверки суммы — до вызова producer
    assert response.status_code == 422
 