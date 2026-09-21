from sqlalchemy import select

from app.models.export import Export
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[Export]):
    model = Export

    async def list_by_inquiry(self, inquiry_id: int) -> list[Export]:
        result = await self.session.execute(
            select(Export).where(Export.inquiry_id == inquiry_id)
        )
        return list(result.scalars().all())
