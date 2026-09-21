from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Data Access層の共通操作。ツール・serviceは直接ORM/SQLを触らずこの層を経由する。"""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: int) -> ModelT | None:
        return await self.session.get(self.model, id)

    async def list(self) -> list[ModelT]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj
