from sqlalchemy import select

from app.models.field import InquiryItemField
from app.repositories.base import BaseRepository


class InquiryItemFieldRepository(BaseRepository[InquiryItemField]):
    model = InquiryItemField

    async def list_by_inquiry_item(
        self, inquiry_item_id: int
    ) -> list[InquiryItemField]:
        result = await self.session.execute(
            select(InquiryItemField).where(
                InquiryItemField.inquiry_item_id == inquiry_item_id
            )
        )
        return list(result.scalars().all())

    async def get_by_item_and_field(
        self, inquiry_item_id: int, field_definition_id: int
    ) -> InquiryItemField | None:
        result = await self.session.execute(
            select(InquiryItemField).where(
                InquiryItemField.inquiry_item_id == inquiry_item_id,
                InquiryItemField.field_definition_id == field_definition_id,
            )
        )
        return result.scalar_one_or_none()
