import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.field import FieldCandidate, InquiryField, InquiryItemField
from app.models.inquiry import Inquiry, InquiryItem
from app.repositories.field_candidate_repository import FieldCandidateRepository
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
        await s.execute(
            delete(InquiryItemField).where(InquiryItemField.id.in_(item_field_ids))
        )
        await s.execute(delete(InquiryItem).where(InquiryItem.id.in_(item_ids)))
        await s.execute(delete(InquiryField).where(InquiryField.id.in_(field_ids)))
        await s.execute(delete(Inquiry).where(Inquiry.id.in_(ids)))
        await s.commit()


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.MOCK_AUTH_TOKEN}"}


async def _seed_review_case_field(
    db_session: AsyncSession, created_inquiry_ids: list[int]
):
    """要確認（conflict、候補2件: 資料由来とWeb由来）のA項目を1件作る。"""
    inquiry = await InquiryRepository(db_session).add(
        Inquiry(inquiry_code=f"INQ-TEST-PATCH-{uuid.uuid4().hex[:8]}", status="draft")
    )
    await db_session.flush()
    created_inquiry_ids.append(inquiry.id)

    definition = (await FieldDefinitionRepository(db_session).list_by_scope("case"))[0]
    field_row = await InquiryFieldRepository(db_session).add(
        InquiryField(
            inquiry_id=inquiry.id,
            field_definition_id=definition.id,
            value=None,
            status="review",
            reason_type="conflict",
        )
    )
    await db_session.flush()

    candidate_repo = FieldCandidateRepository(db_session)
    doc_candidate = await candidate_repo.add(
        FieldCandidate(
            inquiry_field_id=field_row.id,
            value="東西石油開発株式会社",
            source_type="excel",
            source_file="order.xlsx",
            source_location="A2",
        )
    )
    web_candidate = await candidate_repo.add(
        FieldCandidate(
            inquiry_field_id=field_row.id,
            value="東西石油開発（Web）",
            source_type="web",
            web_url="https://example.com",
            web_source_name="公式サイト",
        )
    )
    await db_session.commit()
    return (
        inquiry.id,
        definition.field_id,
        field_row.id,
        doc_candidate.id,
        web_candidate.id,
    )


async def test_patch_case_field_requires_auth(client: AsyncClient) -> None:
    resp = await client.patch(
        "/api/v1/inquiries/1/fields/requester", json={"value": "x"}
    )
    assert resp.status_code == 401


async def test_patch_case_field_confirms_selected_candidate(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    """TEST-12相当: 候補を選んで確定すると ok / confirmed_by=user になる。"""
    (
        inquiry_id,
        field_id,
        field_row_id,
        doc_candidate_id,
        _,
    ) = await _seed_review_case_field(db_session, created_inquiry_ids)

    resp = await client.patch(
        f"/api/v1/inquiries/{inquiry_id}/fields/{field_id}",
        json={
            "value": "東西石油開発株式会社",
            "selected_candidate_id": doc_candidate_id,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["reason_type"] is None
    assert body["confirmed_by"] == "user"
    assert body["is_web_supplemented"] is False

    async with AsyncSessionLocal() as s:
        candidates = (
            (
                await s.execute(
                    select(FieldCandidate).where(
                        FieldCandidate.inquiry_field_id == field_row_id
                    )
                )
            )
            .scalars()
            .all()
        )
        selected = [c for c in candidates if c.is_selected]
        assert len(selected) == 1
        assert selected[0].id == doc_candidate_id


async def test_patch_case_field_recomputes_web_supplemented_for_web_candidate(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id, field_id, _, _, web_candidate_id = await _seed_review_case_field(
        db_session, created_inquiry_ids
    )

    resp = await client.patch(
        f"/api/v1/inquiries/{inquiry_id}/fields/{field_id}",
        json={
            "value": "東西石油開発（Web）",
            "selected_candidate_id": web_candidate_id,
        },
        headers=auth_headers(),
    )
    assert resp.json()["is_web_supplemented"] is True


async def test_patch_case_field_manual_edit_without_candidate(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id, field_id, _, _, _ = await _seed_review_case_field(
        db_session, created_inquiry_ids
    )

    resp = await client.patch(
        f"/api/v1/inquiries/{inquiry_id}/fields/{field_id}",
        json={"value": "手入力した値"},
        headers=auth_headers(),
    )
    body = resp.json()
    assert body["value"] == "手入力した値"
    assert body["status"] == "ok"
    assert body["is_web_supplemented"] is False

    async with AsyncSessionLocal() as session:
        inquiry = await InquiryRepository(session).get(inquiry_id)
        assert inquiry.requester == "手入力した値"


async def test_patch_case_field_empty_value_returns_to_review_missing(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    """TEST-12境界: 空で確定すると要確認（理由missing）に戻る。"""
    inquiry_id, field_id, _, _, _ = await _seed_review_case_field(
        db_session, created_inquiry_ids
    )

    resp = await client.patch(
        f"/api/v1/inquiries/{inquiry_id}/fields/{field_id}",
        json={"value": ""},
        headers=auth_headers(),
    )
    body = resp.json()
    assert body["status"] == "review"
    assert body["reason_type"] == "missing"
    assert body["confirmed_by"] == "user"


async def test_patch_case_field_404_for_unknown_field(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id, _, _, _, _ = await _seed_review_case_field(
        db_session, created_inquiry_ids
    )

    resp = await client.patch(
        f"/api/v1/inquiries/{inquiry_id}/fields/not_a_field",
        json={"value": "x"},
        headers=auth_headers(),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "FIELD_NOT_FOUND"


async def test_patch_item_field_confirms_value(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry = await InquiryRepository(db_session).add(
        Inquiry(inquiry_code=f"INQ-TEST-PATCH-{uuid.uuid4().hex[:8]}", status="draft")
    )
    await db_session.flush()
    created_inquiry_ids.append(inquiry.id)
    item = await InquiryItemRepository(db_session).add(
        InquiryItem(inquiry_id=inquiry.id, item_no=1)
    )
    await db_session.flush()
    definition = (await FieldDefinitionRepository(db_session).list_by_scope("item"))[0]
    await InquiryItemFieldRepository(db_session).add(
        InquiryItemField(
            inquiry_item_id=item.id,
            field_definition_id=definition.id,
            value=None,
            status="review",
            reason_type="missing",
        )
    )
    await db_session.commit()

    resp = await client.patch(
        f"/api/v1/inquiries/{inquiry.id}/items/{item.id}/fields/{definition.field_id}",
        json={"value": "シームレス"},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["value"] == "シームレス"
    assert body["status"] == "ok"
    assert body["confirmed_by"] == "user"
