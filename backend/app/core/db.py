from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _to_async_url(url: str) -> str:
    # psycopg (v3) はネイティブに async 対応。SQLAlchemy 2.0 は "postgresql+psycopg://" を
    # create_async_engine と組み合わせて使うことで AsyncConnection を発行できる
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_async_engine(_to_async_url(settings.DATABASE_URL), echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
