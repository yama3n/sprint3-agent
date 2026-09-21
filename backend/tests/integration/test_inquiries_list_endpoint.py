import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.field import InquiryField
from app.models.inquiry import Inquiry
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_repository import InquiryRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def created_inquiry_ids():
    """endpointテストはclientが別セッション/接続で読むため commit が必要（rollback不可）。
    このfixtureがテスト終了後に子→親の順で確実に後始末する。"""
    ids: list[int] = []
    yield ids
    if not ids:
        return
    async with AsyncSessionLocal() as cleanup_session:
        await cleanup_session.execute(
            delete(InquiryField).where(InquiryField.inquiry_id.in_(ids))
        )
        await cleanup_session.execute(delete(Inquiry).where(Inquiry.id.in_(ids)))
        await cleanup_session.commit()


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.MOCK_AUTH_TOKEN}"}


async def test_list_inquiries_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/inquiries")
    assert resp.status_code == 401


async def test_list_inquiries_returns_items_with_review_count(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry = await InquiryRepository(db_session).add(
        Inquiry(
            inquiry_code="INQ-TEST-LIST-0001",
            requester="東西石油開発",
            project_name="北海油田 鋼管更新案件",
            status="draft",
        )
    )
    await db_session.flush()
    created_inquiry_ids.append(inquiry.id)
    field_def = (await FieldDefinitionRepository(db_session).list_by_scope("case"))[0]
    await InquiryFieldRepository(db_session).add(
        InquiryField(
            inquiry_id=inquiry.id, field_definition_id=field_def.id, status="review"
        )
    )
    await db_session.commit()

    resp = await client.get("/api/v1/inquiries", headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()
    match = next(i for i in body["items"] if i["inquiry_code"] == "INQ-TEST-LIST-0001")
    assert match["requester"] == "東西石油開発"
    assert match["review_count"] == 1
    assert match["status"] == "draft"
    assert body["total_count"] >= 1


async def test_list_inquiries_filters_by_status(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    obj = await InquiryRepository(db_session).add(
        Inquiry(inquiry_code="INQ-TEST-LIST-0002", status="final")
    )
    await db_session.flush()
    created_inquiry_ids.append(obj.id)
    await db_session.commit()

    resp = await client.get("/api/v1/inquiries?status=final", headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert all(i["status"] == "final" for i in body["items"])
    assert any(i["inquiry_code"] == "INQ-TEST-LIST-0002" for i in body["items"])
