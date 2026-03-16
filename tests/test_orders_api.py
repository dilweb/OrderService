"""
Тесты для эндпоинта POST /api/orders.

Теория:
- TestClient — отправляет HTTP-запросы в приложение без реального сервера и сети.
- patch + AsyncMock — подменяет Kafka producer, чтобы тест не зависел от внешнего сервиса.
- Три сценария: успех (202), неверная сумма (422), сбой Kafka (503).
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from src.main import app


# Тело запроса, которое проходит все проверки:
# items: 1 товар × цена 10.00 × кол-во 2 = 20.00 == amount
VALID_ORDER = {
    "user_id": 1,
    "items": [
        {"product_id": 1, "name": "Чай", "price": "10.00", "quantity": 2}
    ],
    "currency": "USD",
    "amount": "20.00",
}


@pytest.fixture
def mock_producer():
    """
    Мок-producer: все методы — AsyncMock (поддерживают await).
    По умолчанию publish_event возвращает True (успех).
    """
    producer = AsyncMock()
    producer.publish_event.return_value = True
    return producer


@pytest.fixture
def client(mock_producer):
    """
    TestClient с подменённым Kafka producer.

    patch нужен в двух местах:
    - src.main           → get_producer вызывается в lifespan при старте приложения
    - orderservice.api.routers → get_producer вызывается в обработчике запроса

    Оба патча используют один и тот же mock_producer.
    """
    with (
        patch("src.main.get_producer", return_value=mock_producer),
        patch("orderservice.api.routers.get_producer", return_value=mock_producer),
    ):
        with TestClient(app) as c:
            yield c


# --- Тесты ---


def test_create_order_success_returns_202(client):
    """Валидный запрос с корректной суммой → 202 Accepted с нужными полями."""
    # Act
    response = client.post("/api/orders", json=VALID_ORDER)

    # Assert
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "order_id" in data
    assert "saga_id" in data
    assert "message_id" in data


def test_create_order_amount_mismatch_returns_422(client):
    """
    amount не совпадает с суммой items → роутер отклоняет с 422.
    items дают 10.00 * 2 = 20.00, но amount указан 99.99.
    """
    order = {**VALID_ORDER, "amount": "99.99"}

    response = client.post("/api/orders", json=order)

    assert response.status_code == 422


def test_create_order_kafka_failure_returns_503(client, mock_producer):
    """
    Kafka producer вернул False (не смог доставить) → 503 Service Unavailable.
    Переопределяем поведение мока прямо в тесте.
    """
    mock_producer.publish_event.return_value = False

    response = client.post("/api/orders", json=VALID_ORDER)

    assert response.status_code == 503
 