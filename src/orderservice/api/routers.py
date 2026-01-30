import logging
from fastapi import APIRouter, status, HTTPException

from orderservice.models.order import OrderCreate, OrderAccepted
from orderservice.kafka.producer import get_producer

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/orders", response_model=OrderAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_order(order: OrderCreate) -> OrderAccepted:
    """
    Принимает заказ от пользователя и отправляет его в Kafka топик orders
    
    Returns:
        OrderAccepted: Подтверждение приёма заказа
    """
    producer = get_producer()
    
    order_data = order.model_dump()
    
    success = producer.publish_order(order_data)
    
    if not success:
        logger.error(f"Не удалось отправить заказ {order.order_id} в Kafka")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис временно недоступен. Попробуйте позже."
        )
    
    return OrderAccepted(order_id=order.order_id, status="accepted")