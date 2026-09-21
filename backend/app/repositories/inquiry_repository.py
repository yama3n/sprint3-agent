from sqlalchemy import select

from app.models.inquiry import Inquiry
from app.repositories.base import BaseRepository


class InquiryRepository(BaseRepository[Inquiry]):
    model = Inquiry

    async def get_by_code(self, inquiry_code: str) -> Inquiry | None:
        result = await self.session.execute(
            select(Inquiry).where(Inquiry.inquiry_code == inquiry_code)
        )
        return result.scalar_one_or_none()
