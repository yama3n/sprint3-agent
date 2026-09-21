import uuid
from pathlib import Path

from httpx import AsyncClient
from pytest import MonkeyPatch

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.agent_run import AgentRun
from app.models.inquiry import Inquiry, InquiryFile
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.inquiry_file_repository import InquiryFileRepository
from app.repositories.inquiry_repository import InquiryRepository


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.MOCK_AUTH_TOKEN}"}


async def test_delete_inquiry_requires_auth(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/inquiries/1")
    assert response.status_code == 401


async def test_delete_inquiry_removes_the_inquiry_and_related_rows(
    client: AsyncClient,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    uploaded_file = tmp_path / "delete-me.xlsx"
    uploaded_file.write_bytes(b"test")
    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))

    async with AsyncSessionLocal() as session:
        inquiry = await InquiryRepository(session).add(
            Inquiry(inquiry_code=f"INQ-DELETE-{uuid.uuid4().hex[:8]}", status="draft")
        )
        await session.flush()
        await InquiryFileRepository(session).add(
            InquiryFile(
                inquiry_id=inquiry.id,
                file_name="delete-me.xlsx",
                file_type="xlsx",
                storage_path=str(uploaded_file),
            )
        )
        await AgentRunRepository(session).add(
            AgentRun(
                inquiry_id=inquiry.id,
                agent_name="agent01_extraction",
                trigger="new_upload",
                status="failed",
                stage="failed",
            )
        )
        await session.commit()
        inquiry_id = inquiry.id

    response = await client.delete(
        f"/api/v1/inquiries/{inquiry_id}", headers=auth_headers()
    )

    assert response.status_code == 204
    assert not uploaded_file.exists()
    async with AsyncSessionLocal() as session:
        assert await InquiryRepository(session).get(inquiry_id) is None
        assert await InquiryFileRepository(session).list_by_inquiry(inquiry_id) == []
        assert await AgentRunRepository(session).list_by_inquiry(inquiry_id) == []


async def test_delete_inquiry_returns_404_for_unknown_inquiry(
    client: AsyncClient,
) -> None:
    response = await client.delete(
        "/api/v1/inquiries/999999999", headers=auth_headers()
    )
    assert response.status_code == 404
