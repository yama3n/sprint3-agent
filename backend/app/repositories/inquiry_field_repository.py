from sqlalchemy import select

from app.models.field import InquiryField
from app.repositories.base import BaseRepository


class InquiryFieldRepository(BaseRepository[InquiryField]):
    model = InquiryField

    async def list_by_inquiry(self, inquiry_id: int) -> list[InquiryField]:
        result = await self.session.execute(
            select(InquiryField).where(InquiryField.inquiry_id == inquiry_id)
        )
        return list(result.scalars().all())

    async def get_by_inquiry_and_field(
        self, inquiry_id: int, field_definition_id: int
    ) -> InquiryField | None:
        result = await self.session.execute(
            select(InquiryField).where(
                InquiryField.inquiry_id == inquiry_id,
                InquiryField.field_definition_id == field_definition_id,
            )
        )
        return result.scalar_one_or_none()
