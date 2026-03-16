from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import AsyncSessionLocal


async def get_session() -> AsyncSession:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close() 