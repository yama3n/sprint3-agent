import io

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.v1.endpoints.inquiries as inquiries_endpoint
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.agent_run import AgentRun
from app.models.inquiry import Inquiry, InquiryFile


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def no_op_orchestration(monkeypatch: pytest.MonkeyPatch):
    """実エージェント呼び出しを避け、バックグラウンドタスクの起動有無のみ検証する。"""

    calls: list[tuple] = []

    async def fake_new(inquiry_id, agent_run_id, files):
        calls.append(("new", inquiry_id, agent_run_id, len(files)))

    async def fake_additional(inquiry_id, agent_run_id, files):
        calls.append(("additional", inquiry_id, agent_run_id, len(files)))

    monkeypatch.setattr(inquiries_endpoint, "orchestrate_new_upload", fake_new)
    monkeypatch.setattr(
        inquiries_endpoint, "orchestrate_additional_upload", fake_additional
    )
    return calls


@pytest.fixture
async def created_inquiry_ids():
    ids: list[int] = []
    yield ids
    if not ids:
        return
    async with AsyncSessionLocal() as cleanup_session:
        file_ids_res = await cleanup_session.execute(
            InquiryFile.__table__.select().where(InquiryFile.inquiry_id.in_(ids))
        )
        file_ids = [row.id for row in file_ids_res.fetchall()]
        from app.models.agent_run import ParsedDocument

        await cleanup_session.execute(
            delete(ParsedDocument).where(ParsedDocument.file_id.in_(file_ids))
        )
        await cleanup_session.execute(
            delete(AgentRun).where(AgentRun.inquiry_id.in_(ids))
        )
        await cleanup_session.execute(
            delete(InquiryFile).where(InquiryFile.inquiry_id.in_(ids))
        )
        await cleanup_session.execute(delete(Inquiry).where(Inquiry.id.in_(ids)))
        await cleanup_session.commit()


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.MOCK_AUTH_TOKEN}"}


async def test_create_inquiry_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/inquiries",
        files={"files": ("a.xlsx", io.BytesIO(b"x"), "application/octet-stream")},
    )
    assert resp.status_code == 401


async def test_create_inquiry_rejects_unsupported_file_type(
    client: AsyncClient, no_op_orchestration
) -> None:
    resp = await client.post(
        "/api/v1/inquiries",
        files={
            "files": ("contract.docx", io.BytesIO(b"x"), "application/octet-stream")
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "UNSUPPORTED_FILE_TYPE"


async def test_create_inquiry_returns_202_and_schedules_orchestration(
    client: AsyncClient, no_op_orchestration, created_inquiry_ids: list[int]
) -> None:
    resp = await client.post(
        "/api/v1/inquiries",
        files=[
            ("files", ("order.xlsx", io.BytesIO(b"dummy"), "application/octet-stream"))
        ],
        headers=auth_headers(),
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "draft"
    assert body["agent_run_id"] > 0
    created_inquiry_ids.append(body["inquiry_id"])

    import asyncio

    await asyncio.sleep(0)
    assert no_op_orchestration and no_op_orchestration[0][0] == "new"


async def test_get_agent_status_returns_latest_stage(
    client: AsyncClient, db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    from app.repositories.agent_run_repository import AgentRunRepository
    from app.repositories.inquiry_repository import InquiryRepository

    inquiry = await InquiryRepository(db_session).add(
        Inquiry(inquiry_code="INQ-TEST-STATUS-0001", status="draft")
    )
    await db_session.flush()
    created_inquiry_ids.append(inquiry.id)
    await AgentRunRepository(db_session).add(
        AgentRun(
            inquiry_id=inquiry.id,
            agent_name="agent01_extraction",
            trigger="new_upload",
            status="running",
            stage="extracting",
            progress_percent=30,
        )
    )
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/inquiries/{inquiry.id}/agent-status", headers=auth_headers()
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stage"] == "extracting"
    assert body["progress_percent"] == 30


async def test_get_agent_status_404_for_unknown_inquiry(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/inquiries/999999999/agent-status", headers=auth_headers()
    )
    assert resp.status_code == 404
