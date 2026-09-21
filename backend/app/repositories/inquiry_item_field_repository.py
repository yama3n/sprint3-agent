from sqlalchemy import func, select

from app.models.field import InquiryItemField
from app.models.inquiry import InquiryItem
from app.repositories.base import BaseRepository


class InquiryItemFieldRepository(BaseRepository[InquiryItemField]):
    model = InquiryItemField

    async def count_review_by_inquiry(self, inquiry_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(InquiryItemField)
            .join(InquiryItem, InquiryItemField.inquiry_item_id == InquiryItem.id)
            .where(
                InquiryItem.inquiry_id == inquiry_id,
                InquiryItemField.status == "review",
            )
        )
        return result.scalar_one()

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
