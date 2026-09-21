import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.field import FieldCandidate, InquiryField, InquiryItemField
from app.models.inquiry import Inquiry, InquiryItem, InquiryNote
from app.repositories.field_candidate_repository import FieldCandidateRepository
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_item_field_repository import InquiryItemFieldRepository
from app.repositories.inquiry_item_repository import InquiryItemRepository
from app.repositories.inquiry_note_repository import InquiryNoteRepository
from app.repositories.inquiry_repository import InquiryRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def created_inquiry_ids():
    ids: list[int] = []
    yield ids
    if not ids:
        return
    async with AsyncSessionLocal() as s:
        field_ids = [
            r[0]
            for r in (
                await s.execute(
                    select(InquiryField.id).where(InquiryField.inquiry_id.in_(ids))
                )
            ).fetchall()
        ]
        item_ids = [
            r[0]
            for r in (
                await s.execute(
                    select(InquiryItem.id).where(InquiryItem.inquiry_id.in_(ids))
                )
            ).fetchall()
        ]
        item_field_ids = [
            r[0]
            for r in (
                await s.execute(
                    select(InquiryItemField.id).where(
                        InquiryItemField.inquiry_item_id.in_(item_ids)
                    )
                )
            ).fetchall()
        ]
        await s.execute(
            delete(FieldCandidate).where(FieldCandidate.inquiry_field_id.in_(field_ids))
        )
        await s.execute(
            delete(FieldCandidate).where(
                FieldCandidate.inquiry_item_field_id.in_(item_field_ids)
            )
        )
        await s.execute(delete(InquiryNote).where(InquiryNote.inquiry_id.in_(ids)))
        await s.execute(
            delete(InquiryItemField).where(InquiryItemField.id.in_(item_field_ids))
        )
        await s.execute(delete(InquiryItem).where(InquiryItem.id.in_(item_ids)))
        await s.execute(delete(InquiryField).where(InquiryField.id.in_(field_ids)))
        await s.execute(delete(Inquiry).where(Inquiry.id.in_(ids)))
        await s.commit()


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.MOCK_AUTH_TOKEN}"}


async def _seed_inquiry(
    db_session: AsyncSession, created_inquiry_ids: list[int]
) -> int:
    inquiry = await InquiryRepository(db_session).add(
        Inquiry(
            inquiry_code=f"INQ-TEST-DETAIL-{uuid.uuid4().hex[:8]}",
            requester="東西石油開発",
            project_name="北海油田 鋼管更新案件",
            status="draft",
        )
    )
    await db_session.flush()
    created_inquiry_ids.append(inquiry.id)

    case_defs = await FieldDefinitionRepository(db_session).list_by_scope("case")
    item_defs = await FieldDefinitionRepository(db_session).list_by_scope("item")

    # 1件目: 確認不要（出典あり）、2件目: 要確認（conflict、候補2件）
    ok_field = await InquiryFieldRepository(db_session).add(
        InquiryField(
            inquiry_id=inquiry.id,
            field_definition_id=case_defs[0].id,
            value="東西石油開発株式会社",
            status="ok",
            confirmed_by="ai",
        )
    )
    review_field = await InquiryFieldRepository(db_session).add(
        InquiryField(
            inquiry_id=inquiry.id,
            field_definition_id=case_defs[1].id,
            value=None,
            status="review",
            reason_type="conflict",
        )
    )
    await db_session.flush()

    candidate_repo = FieldCandidateRepository(db_session)
    await candidate_repo.add(
        FieldCandidate(
            inquiry_field_id=ok_field.id,
            value="東西石油開発株式会社",
            source_type="excel",
            source_file="order.xlsx",
            source_location="A2",
            quoted_text="発注元: 東西石油開発株式会社",
            is_selected=True,
        )
    )
    for value in ("2027年1月", "2027年3月"):
        await candidate_repo.add(
            FieldCandidate(
                inquiry_field_id=review_field.id,
                value=value,
                source_type="pdf",
                source_file="quote.pdf",
                source_location="p.1",
            )
        )

    item = await InquiryItemRepository(db_session).add(
        InquiryItem(inquiry_id=inquiry.id, item_no=1)
    )
    await db_session.flush()
    await InquiryItemFieldRepository(db_session).add(
        InquiryItemField(
            inquiry_item_id=item.id,
            field_definition_id=item_defs[2].id,  # grade
            value="L-80",
            status="ok",
            confirmed_by="ai",
        )
    )
    await InquiryNoteRepository(db_session).add(
        InquiryNote(
            inquiry_id=inquiry.id,
            scope="case",
            content="輸送条件は別途協議",
            source_type="pdf",
            source_file="quote.pdf",
            source_location="p.2",
        )
    )
    await db_session.commit()
    return inquiry.id


async def test_get_detail_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/inquiries/1")
    assert resp.status_code == 401


async def test_get_detail_404_for_unknown_inquiry(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/inquiries/999999999", headers=auth_headers())
    assert resp.status_code == 404
    assert resp.json()["detail"] == "INQUIRY_NOT_FOUND"


async def test_get_detail_returns_fields_candidates_items_and_summary(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id = await _seed_inquiry(db_session, created_inquiry_ids)

    resp = await client.get(f"/api/v1/inquiries/{inquiry_id}", headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()

    assert body["inquiry"]["requester"] == "東西石油開発"
    assert body["inquiry"]["status"] == "draft"

    # 確認不要の項目は出典（候補）付きで返る（FUNC-06）
    ok_field = next(f for f in body["case_fields"] if f["status"] == "ok")
    assert ok_field["label"]  # field_definitionsのlabelが解決されている
    assert ok_field["candidates"][0]["source_file"] == "order.xlsx"
    assert ok_field["confirmed_by"] == "ai"

    # 要確認の項目は理由と複数候補を保持（FUNC-07 / TEST-03相当）
    review_field = next(f for f in body["case_fields"] if f["status"] == "review")
    assert review_field["reason_type"] == "conflict"
    assert len(review_field["candidates"]) == 2
    assert review_field["value"] is None

    assert body["items"][0]["item_no"] == 1
    assert any(f["value"] == "L-80" for f in body["items"][0]["fields"])
    assert body["case_notes"][0]["content"] == "輸送条件は別途協議"
    assert body["review_summary"]["review_count"] == 1


async def test_get_detail_sorts_case_fields_by_display_order(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id = await _seed_inquiry(db_session, created_inquiry_ids)

    resp = await client.get(f"/api/v1/inquiries/{inquiry_id}", headers=auth_headers())
    orders = [f["display_order"] for f in resp.json()["case_fields"]]
    assert orders == sorted(orders)
