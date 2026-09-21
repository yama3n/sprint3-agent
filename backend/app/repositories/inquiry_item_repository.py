from sqlalchemy import select

from app.models.inquiry import InquiryItem
from app.repositories.base import BaseRepository


class InquiryItemRepository(BaseRepository[InquiryItem]):
    model = InquiryItem

    async def list_by_inquiry(self, inquiry_id: int) -> list[InquiryItem]:
        result = await self.session.execute(
            select(InquiryItem)
            .where(InquiryItem.inquiry_id == inquiry_id)
            .order_by(InquiryItem.item_no)
        )
        return list(result.scalars().all())
