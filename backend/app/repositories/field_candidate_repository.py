from sqlalchemy import select

from app.models.field import FieldCandidate
from app.repositories.base import BaseRepository


class FieldCandidateRepository(BaseRepository[FieldCandidate]):
    model = FieldCandidate

    async def list_by_inquiry_field(
        self, inquiry_field_id: int
    ) -> list[FieldCandidate]:
        result = await self.session.execute(
            select(FieldCandidate).where(
                FieldCandidate.inquiry_field_id == inquiry_field_id
            )
        )
        return list(result.scalars().all())

    async def list_by_inquiry_item_field(
        self, inquiry_item_field_id: int
    ) -> list[FieldCandidate]:
        result = await self.session.execute(
            select(FieldCandidate).where(
                FieldCandidate.inquiry_item_field_id == inquiry_item_field_id
            )
        )
        return list(result.scalars().all())
