import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.inquiry import (
    AgentStatusResponse,
    InquiryListResponse,
    UploadResponse,
)
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.services import inquiry_service
from app.services.agent_orchestrator import (
    orchestrate_additional_upload,
    orchestrate_new_upload,
)
from app.services.inquiry_service import AgentStatusNotFoundError, InquiryNotFoundError
from app.services.inquiry_upload_service import (
    NoFilesError,
    UnsupportedFileTypeError,
    add_files_to_inquiry,
    create_inquiry_with_files,
)

router = APIRouter(prefix="/inquiries", tags=["Inquiries"])


@router.get("", response_model=InquiryListResponse)
async def list_inquiries(
    status: Literal["draft", "final"] | None = None,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> InquiryListResponse:
    return await inquiry_service.list_inquiries(session, status=status)


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=UploadResponse)
async def create_inquiry(
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> UploadResponse:
    """FUNC-01 新規アップロード。202を即返し、AGENT-01→AGENT-02はバックグラウンドで進む
    （agent-development.md: HTTPで完了を同期待ちしない）。"""
    try:
        inquiry, inquiry_files, agent_run = await create_inquiry_with_files(
            session, files
        )
    except NoFilesError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NO_FILES") from None
    except UnsupportedFileTypeError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_FILE_TYPE"
        ) from None

    task = asyncio.create_task(
        orchestrate_new_upload(inquiry.id, agent_run.id, inquiry_files)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return UploadResponse(
        inquiry_id=inquiry.id, status="draft", agent_run_id=agent_run.id
    )


@router.post(
    "/{inquiry_id}/files",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=UploadResponse,
)
async def add_files(
    inquiry_id: int,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> UploadResponse:
    """FUNC-01 追加アップロード（SCR-05）。"""
    from app.repositories.inquiry_repository import InquiryRepository

    inquiry = await InquiryRepository(session).get(inquiry_id)
    if inquiry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND")

    try:
        inquiry_files, agent_run = await add_files_to_inquiry(
            session, inquiry_id, files
        )
    except NoFilesError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NO_FILES") from None
    except UnsupportedFileTypeError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_FILE_TYPE"
        ) from None

    task = asyncio.create_task(
        orchestrate_additional_upload(inquiry_id, agent_run.id, inquiry_files)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return UploadResponse(
        inquiry_id=inquiry_id, status="draft", agent_run_id=agent_run.id
    )


@router.get("/{inquiry_id}/agent-status", response_model=AgentStatusResponse)
async def get_agent_status(
    inquiry_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> AgentStatusResponse:
    try:
        return await inquiry_service.get_agent_status(session, inquiry_id)
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None
    except AgentStatusNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="AGENT_STATUS_NOT_FOUND"
        ) from None


# バックグラウンドタスクへの強参照を保持する（asyncio.create_task()の戻り値をどこにも
# 保持しないとGCで消える可能性があるため。FastAPIのBackgroundTasksはレスポンス送信後に
# 実行される点は同じだが、こちらは即座にスケジュールしaccepted応答は待たない）
_background_tasks: set[asyncio.Task] = set()
