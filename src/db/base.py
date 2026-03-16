from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.settings import get_db_url


class Base(DeclarativeBase):
    pass


engine = create_async_engine(get_db_url(), echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def close_db() -> None:
    await engine.dispose() 