"""
Нагрузочный тест для POST /api/orders.

Требования:
- Приложение должно быть запущено: poetry run uvicorn src.main:app --port 8000
- Kafka должна быть запущена: docker compose -f docker-compose.test.yml up -d

Запуск с веб-интерфейсом:
    locust -f locustfile.py --host http://localhost:8000

Запуск без интерфейса (headless), например в CI:
    locust -f locustfile.py --host http://localhost:8000 \
           --headless -u 50 -r 10 --run-time 30s

Параметры:
    -u  — общее количество виртуальных пользователей
    -r  — скорость добавления пользователей (users/sec)
    --run-time — длительность теста
"""

from locust import HttpUser, between, task
from decimal import Decimal
import random


class OrderServiceUser(HttpUser):
    # Пауза между запросами одного виртуального пользователя (секунды)
    wait_time = between(0.5, 2)

    @task(weight=3)
    def create_valid_order(self):
        """
        Основной сценарий: валидный заказ → 202 Accepted.
        weight=3 означает что этот task будет вызываться в 3 раза чаще остальных.
        """
        quantity = random.randint(1, 5)
        price = round(random.uniform(5.0, 100.0), 2)
        amount = round(price * quantity, 2)

        self.client.post(
            "/api/orders",
            json={
                "user_id": random.randint(1, 1000),
                "items": [
                    {
                        "product_id": random.randint(1, 100),
                        "name": "Тестовый товар",
                        "price": str(price),
                        "quantity": quantity,
                    }
                ],
                "currency": random.choice(["USD", "KZT", "RUB", "UAH"]),
                "amount": str(amount),
            },
            # name группирует запросы в статистике под одним именем
            name="POST /api/orders [valid]",
        )

    @task(weight=1)
    def create_order_with_wrong_amount(self):
        """
        Сценарий ошибки: неверная сумма → 422.
        weight=1 — реже чем успешные запросы.
        Проверяем что роутер быстро отклоняет невалидные данные.
        """
        self.client.post(
            "/api/orders",
            json={
                "user_id": 1,
                "items": [
                    {
                        "product_id": 1,
                        "name": "Товар",
                        "price": "10.00",
                        "quantity": 2,
                    }
                ],
                "currency": "USD",
                "amount": "999.99",  # намеренно неверная сумма
            },
            # catch_response=False — 422 не считается ошибкой locust
            name="POST /api/orders [invalid amount]",
        )
 