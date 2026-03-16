"""
Юнит-тесты для Kafka consumer: десериализация сообщений.

Теория:
- Тестируем только статический метод _deserialize(bytes) -> dict.
- Не подключаемся к реальному Kafka — только проверяем преобразование данных.
- На проде такие тесты в CI гарантируют, что контракт формата сообщений не сломан.
"""

import pytest

from orderservice.kafka.consumer import OrderKafkaConsumer


def test_deserialize_valid_json():
    """Валидный JSON в bytes превращается в dict."""
    # Arrange
    payload = b'{"order_id": "123", "user_id": 1}'
    # Act
    result = OrderKafkaConsumer._deserialize(payload)
    # Assert
    assert result == {"order_id": "123", "user_id": 1}


def test_deserialize_empty_bytes_returns_empty_dict():
    """Пустой value возвращает {} (как в коде consumer)."""
    assert OrderKafkaConsumer._deserialize(b"") == {}


def test_deserialize_utf8():
    """Сообщение в UTF-8 корректно декодируется."""
    payload = '{"name": "Чай"}'.encode("utf-8")
    result = OrderKafkaConsumer._deserialize(payload)
    assert result["name"] == "Чай"


def test_deserialize_nested_structure():
    """Вложенная структура (как order payload) десериализуется полностью."""
    payload = b'{"order_id": "abc", "payload": {"items": [{"id": 1}]}}'
    result = OrderKafkaConsumer._deserialize(payload)
    assert result["order_id"] == "abc"
    assert result["payload"]["items"][0]["id"] == 1


def test_deserialize_invalid_json_raises():
    """Невалидный JSON приводит к ошибке (json.loads выбросит)."""
    with pytest.raises((ValueError, TypeError)):
        OrderKafkaConsumer._deserialize(b"not json at all")
 