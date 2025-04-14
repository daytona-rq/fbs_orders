from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.database.config import settings

engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
    pool_size=5,
    max_overflow=10
)


session_factory = async_sessionmaker(engine)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass


