import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.field import InquiryField, InquiryItemField
from app.models.inquiry import Inquiry, InquiryItem
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_item_field_repository import InquiryItemFieldRepository
from app.repositories.inquiry_item_repository import InquiryItemRepository
from app.repositories.inquiry_repository import InquiryRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def inquiry(db_session: AsyncSession) -> Inquiry:
    obj = await InquiryRepository(db_session).add(
        Inquiry(inquiry_code="INQ-TEST-REVIEW-0001", status="draft")
    )
    await db_session.flush()
    return obj


async def test_inquiry_field_repository_counts_only_review_status(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    case_fields = await FieldDefinitionRepository(db_session).list_by_scope("case")
    repo = InquiryFieldRepository(db_session)
    await repo.add(
        InquiryField(
            inquiry_id=inquiry.id,
            field_definition_id=case_fields[0].id,
            status="review",
        )
    )
    await repo.add(
        InquiryField(
            inquiry_id=inquiry.id,
            field_definition_id=case_fields[1].id,
            status="review",
        )
    )
    await repo.add(
        InquiryField(
            inquiry_id=inquiry.id, field_definition_id=case_fields[2].id, status="ok"
        )
    )
    await db_session.flush()

    count = await repo.count_review_by_inquiry(inquiry.id)
    assert count == 2


async def test_inquiry_item_field_repository_counts_review_across_items(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    item_fields = await FieldDefinitionRepository(db_session).list_by_scope("item")
    item_repo = InquiryItemRepository(db_session)
    item1 = await item_repo.add(InquiryItem(inquiry_id=inquiry.id, item_no=1))
    item2 = await item_repo.add(InquiryItem(inquiry_id=inquiry.id, item_no=2))
    await db_session.flush()

    repo = InquiryItemFieldRepository(db_session)
    await repo.add(
        InquiryItemField(
            inquiry_item_id=item1.id,
            field_definition_id=item_fields[0].id,
            status="review",
        )
    )
    await repo.add(
        InquiryItemField(
            inquiry_item_id=item2.id,
            field_definition_id=item_fields[0].id,
            status="review",
        )
    )
    await repo.add(
        InquiryItemField(
            inquiry_item_id=item2.id, field_definition_id=item_fields[1].id, status="ok"
        )
    )
    await db_session.flush()

    count = await repo.count_review_by_inquiry(inquiry.id)
    assert count == 2
