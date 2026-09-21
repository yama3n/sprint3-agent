import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import FileResponse

from app.api.v1.schemas.inquiry import (
    AgentStatusResponse,
    ConfirmResponse,
    ExportRequest,
    ExportResponse,
    FieldUpdateRequest,
    FieldUpdateResponse,
    InquiryDetailResponse,
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
from app.services.export_service import (
    ExportNotFoundError,
    UnsupportedExportFormatError,
    confirm_inquiry,
    create_export,
    get_export_file,
)
from app.services.inquiry_service import (
    AgentStatusNotFoundError,
    FieldNotFoundError,
    InquiryNotFoundError,
    ItemNotFoundError,
)
from app.services.inquiry_deletion_service import delete_inquiry
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


@router.get("/{inquiry_id}", response_model=InquiryDetailResponse)
async def get_inquiry_detail(
    inquiry_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> InquiryDetailResponse:
    try:
        return await inquiry_service.get_inquiry_detail(session, inquiry_id)
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None


@router.delete("/{inquiry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_inquiry(
    inquiry_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> None:
    """引合と、その引合だけに属する関連データ・管理対象ファイルを削除する。"""
    try:
        await delete_inquiry(session, inquiry_id)
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None


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


@router.patch("/{inquiry_id}/fields/{field_id}", response_model=FieldUpdateResponse)
async def update_case_field(
    inquiry_id: int,
    field_id: str,
    payload: FieldUpdateRequest,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> FieldUpdateResponse:
    """FUNC-08 A項目の値修正・確定（SCR-04 確認・修正モード）。"""
    try:
        return await inquiry_service.update_case_field(
            session,
            inquiry_id,
            field_id,
            value=payload.value,
            selected_candidate_id=payload.selected_candidate_id,
        )
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None
    except FieldNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="FIELD_NOT_FOUND"
        ) from None


@router.patch(
    "/{inquiry_id}/items/{item_id}/fields/{field_id}",
    response_model=FieldUpdateResponse,
)
async def update_item_field(
    inquiry_id: int,
    item_id: int,
    field_id: str,
    payload: FieldUpdateRequest,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> FieldUpdateResponse:
    """FUNC-08 B項目（品目ごと）の値修正・確定（SCR-04 確認・修正モード）。"""
    try:
        return await inquiry_service.update_item_field(
            session,
            inquiry_id,
            item_id,
            field_id,
            value=payload.value,
            selected_candidate_id=payload.selected_candidate_id,
        )
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None
    except ItemNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="ITEM_NOT_FOUND"
        ) from None
    except FieldNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="FIELD_NOT_FOUND"
        ) from None


@router.post("/{inquiry_id}/confirm", response_model=ConfirmResponse)
async def confirm(
    inquiry_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> ConfirmResponse:
    """FUNC-09 成果物確定。MVPではロック・確定解除・版管理は行わない（再確定も許容）。"""
    try:
        return await confirm_inquiry(session, inquiry_id)
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None


@router.post("/{inquiry_id}/exports", response_model=ExportResponse)
async def create_inquiry_export(
    inquiry_id: int,
    payload: ExportRequest,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> ExportResponse:
    """FUNC-05 成果物生成（Scope 1はExcelのみ。Word/PDFはScope 2で400）。"""
    try:
        return await create_export(session, inquiry_id, payload.format)
    except UnsupportedExportFormatError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_FORMAT"
        ) from None
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None


@router.get("/{inquiry_id}/exports/{export_id}/download")
async def download_inquiry_export(
    inquiry_id: int,
    export_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> FileResponse:
    """FUNC-05 成果物のダウンロード（Content-Disposition: attachment）。"""
    try:
        path, file_name = await get_export_file(session, inquiry_id, export_id)
    except InquiryNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="INQUIRY_NOT_FOUND"
        ) from None
    except ExportNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="EXPORT_NOT_FOUND"
        ) from None

    return FileResponse(
        path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# バックグラウンドタスクへの強参照を保持する（asyncio.create_task()の戻り値をどこにも
# 保持しないとGCで消える可能性があるため。FastAPIのBackgroundTasksはレスポンス送信後に
# 実行される点は同じだが、こちらは即座にスケジュールしaccepted応答は待たない）
_background_tasks: set[asyncio.Task] = set()
