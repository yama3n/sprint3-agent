import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.inquiry import Inquiry
from app.repositories.inquiry_repository import InquiryRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


async def test_add_and_get_by_code(db_session: AsyncSession) -> None:
    repo = InquiryRepository(db_session)
    inquiry = Inquiry(inquiry_code="INQ-TEST-0001", requester="テスト株式会社", status="draft")

    await repo.add(inquiry)
    await db_session.flush()

    found = await repo.get_by_code("INQ-TEST-0001")
    assert found is not None
    assert found.requester == "テスト株式会社"
    assert found.status == "draft"
