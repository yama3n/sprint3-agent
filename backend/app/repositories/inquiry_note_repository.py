from sqlalchemy import select

from app.models.inquiry import InquiryNote
from app.repositories.base import BaseRepository


class InquiryNoteRepository(BaseRepository[InquiryNote]):
    model = InquiryNote

    async def list_by_inquiry(self, inquiry_id: int) -> list[InquiryNote]:
        result = await self.session.execute(
            select(InquiryNote).where(InquiryNote.inquiry_id == inquiry_id)
        )
        return list(result.scalars().all())
