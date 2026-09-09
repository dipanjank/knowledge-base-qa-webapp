from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

_async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_async_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session


def create_sync_session_factory(database_url: str) -> sessionmaker:
    """Create a sync sessionmaker for use by PostgresChatMessageHistory."""
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    sync_engine = create_engine(sync_url)
    return sessionmaker(sync_engine, expire_on_commit=False)
