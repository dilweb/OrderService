
import asyncio
from contextlib import asynccontextmanager
import logging
import os
import time

from aiokafka.errors import KafkaConnectionError
from fastapi import FastAPI, Request
import uvicorn

from orderservice.api.routers import router
from orderservice.kafka.producer import get_producer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

MAX_CONNECT_ATTEMPTS = int(os.getenv("KAFKA_CONNECT_MAX_ATTEMPTS", "10"))
CONNECT_BASE_DELAY = float(os.getenv("KAFKA_CONNECT_RETRY_DELAY", "1.0"))


def _max_delay(current: float) -> float:
    return min(current * 2, 30.0)


async def _start_producer_with_retry(producer) -> None:
    delay = CONNECT_BASE_DELAY
    for attempt in range(1, MAX_CONNECT_ATTEMPTS + 1):
        try:
            await producer.start()
            return
        except KafkaConnectionError:
            logger.warning(
                "Kafka connection attempt %s/%s failed, retrying in %.1fs",
                attempt,
                MAX_CONNECT_ATTEMPTS,
                delay,
            )
            if attempt == MAX_CONNECT_ATTEMPTS:
                raise
            await asyncio.sleep(delay)
            delay = _max_delay(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle hook для FastAPI: инициализируем Kafka продьюсер перед запуском
    и аккуратно останавливаем после завершения.
    """
    logger.info("Order Service запускается...")
    producer = get_producer()
    await _start_producer_with_retry(producer)
    logger.info("Order Service готов принимать запросы")

    yield

    logger.info("Order Service завершает работу...")
    await producer.stop()
    logger.info("Order Service остановлен")


app = FastAPI(
    title="Order Service",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "HTTP %s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(router, prefix="/api", tags=["orders"])


def start_app():
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_app()
