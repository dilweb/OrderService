"""
Юнит-тесты для моделей заказа (orderservice.models.order).

Теория:
- Тестируем одну единицу логики — метод calculate_total() и валидацию моделей.
- Никакой БД, Kafka, HTTP — только входные данные и результат (AAA: Arrange, Act, Assert).
- Такие тесты на проде запускаются в CI перед деплоем и не требуют окружения.
"""

import pytest
from decimal import Decimal

from orderservice.models.order import OrderCreate, OrderItem


# --- calculate_total() ---


def test_calculate_total_one_item():
    """Один товар: price * quantity = total."""
    # Arrange
    order = OrderCreate(
        user_id=1,
        items=[
            OrderItem(product_id=1, name="Чай", price=Decimal("10.50"), quantity=2)
        ],
        currency="USD",
        amount=Decimal("21.00"),
    )
    # Act
    total = order.calculate_total()
    # Assert
    assert total == Decimal("21.00")


def test_calculate_total_several_items():
    """Несколько позиций: сумма (price * quantity) по всем items."""
    # Arrange
    order = OrderCreate(
        user_id=1,
        items=[
            OrderItem(product_id=1, name="Чай", price=Decimal("10.00"), quantity=2),
            OrderItem(product_id=2, name="Кофе", price=Decimal("5.50"), quantity=3),
        ],
        currency="KZT",
        amount=Decimal("36.50"),
    )
    # Act
    total = order.calculate_total()
    # Assert
    assert total == Decimal("36.50")  # 20.00 + 16.50


@pytest.mark.parametrize(
    "price,quantity,expected",
    [
        (Decimal("1"), 1, Decimal("1")),
        (Decimal("0.01"), 100, Decimal("1.00")),
        (Decimal("99.99"), 2, Decimal("199.98")),
    ],
)
def test_calculate_total_parametrized(price, quantity, expected):
    """Параметризованный тест: несколько комбинаций price/quantity."""
    order = OrderCreate(
        user_id=1,
        items=[OrderItem(product_id=1, name="X", price=price, quantity=quantity)],
        currency="RUB",
        amount=expected,
    )
    assert order.calculate_total() == expected


# --- Валидация Pydantic (поведение моделей) ---


def test_order_item_rejects_zero_price():
    """OrderItem не должен принимать price <= 0 (Field(..., gt=0))."""
    with pytest.raises(ValueError):
        OrderItem(product_id=1, name="X", price=Decimal("0"), quantity=1)


def test_order_item_rejects_negative_quantity():
    """OrderItem не должен принимать quantity <= 0."""
    with pytest.raises(ValueError):
        OrderItem(product_id=1, name="X", price=Decimal("1"), quantity=0)


def test_order_create_requires_at_least_one_item():
    """OrderCreate требует min_length=1 для items."""
    with pytest.raises(ValueError):
        OrderCreate(
            user_id=1,
            items=[],
            currency="USD",
            amount=Decimal("10"),
        )


def test_order_create_accepts_valid_currency():
    """OrderCreate принимает только USD, KZT, UAH, RUB."""
    order = OrderCreate(
        user_id=1,
        items=[OrderItem(product_id=1, name="X", price=Decimal("1"), quantity=1)],
        currency="UAH",
        amount=Decimal("1"),
    )
    assert order.currency == "UAH" 