from sqlalchemy import select

from app.models.inquiry import InquiryFile
from app.repositories.base import BaseRepository


class InquiryFileRepository(BaseRepository[InquiryFile]):
    model = InquiryFile

    async def list_by_inquiry(self, inquiry_id: int) -> list[InquiryFile]:
        result = await self.session.execute(
            select(InquiryFile).where(InquiryFile.inquiry_id == inquiry_id)
        )
        return list(result.scalars().all())
