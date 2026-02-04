import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from orderservice.kafka.producer import get_producer
from orderservice.models.order import (
    OrderAccepted,
    OrderCreate,
    OrderEvent,
    OrderPayload,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/orders", response_model=OrderAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_order(order: OrderCreate) -> OrderAccepted:
    """Принять запрос на создание заказа и отправить событие order.created в Kafka."""
    producer = get_producer()

    calculated_total = order.calculate_total()
    if calculated_total != order.amount:
        logger.warning(
            "Order amount mismatch: expected %s, got %s", calculated_total, order.amount
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Сумма order.amount должна равняться сумме позиций",
        )

    order_id = uuid4()
    saga_id = uuid4()
    message_id = uuid4()
    payload = OrderPayload(
        **order.model_dump(),
        created_at=datetime.now(timezone.utc),
        total=calculated_total,
    )
    event = OrderEvent(
        order_id=order_id,
        saga_id=saga_id,
        message_id=message_id,
        payload=payload,
    )

    success = await producer.publish_event(event.model_dump(mode="json"))
    if not success:
        logger.error("Не удалось опубликовать событие order.created для %s", order_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ошибка публикации события. Попробуйте позже.",
        )

    logger.info("Order %s accepted (saga=%s, message=%s)", order_id, saga_id, message_id)
    return OrderAccepted(order_id=order_id, saga_id=saga_id, message_id=message_id)
