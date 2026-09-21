"""FUNC-01 書類アップロード・引合自動生成（05-api-ipo.md POST /inquiries, /inquiries/{id}/files）。

ファイル保存・DBレコード作成は決定論的処理。AGENT-01/AGENT-02の起動は agent_orchestrator.py
（service層からjobs.start_agent_job()経由）に委譲する（agent-development.md: endpointsから
run_agent()を直接呼ばない）。
"""

import datetime
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.agent_run import AgentRun
from app.models.inquiry import Inquiry, InquiryFile
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.inquiry_file_repository import InquiryFileRepository
from app.repositories.inquiry_repository import InquiryRepository

SUPPORTED_EXTENSIONS = {"xlsx": "xlsx", "pdf": "pdf", "eml": "eml"}


class NoFilesError(Exception):
    pass


class UnsupportedFileTypeError(Exception):
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        super().__init__(f"UNSUPPORTED_FILE_TYPE: {file_name}")


def _extension(file_name: str) -> str:
    return file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""


def validate_file_names(file_names: list[str]) -> None:
    """05-api-ipo.md: 400 UNSUPPORTED_FILE_TYPE / NO_FILES の判定（決定論的処理）。"""
    if not file_names:
        raise NoFilesError("NO_FILES")
    for name in file_names:
        if _extension(name) not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(name)


def _generate_inquiry_code() -> str:
    year = datetime.datetime.now(datetime.UTC).year
    # PoC簡易採番: 年+ランダム4桁（並行アップロードでの衝突を避けるため連番でなく乱数を使用）
    return f"INQ-{year}-{uuid.uuid4().int % 10000:04d}"


def _storage_dir_for(inquiry_id: int) -> Path:
    path = Path(settings.STORAGE_DIR) / "inquiries" / str(inquiry_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _save_upload(file: UploadFile, dest_dir: Path) -> str:
    dest_path = dest_dir / file.filename
    content = await file.read()
    dest_path.write_bytes(content)
    return str(dest_path)


async def create_inquiry_with_files(
    session: AsyncSession, files: list[UploadFile]
) -> tuple[Inquiry, list[InquiryFile], AgentRun]:
    """FUNC-01新規アップロード: Inquiry + InquiryFile を作成しファイルを保存する。
    agent-plan.md §2 stage表どおり、受付時にAGENT-01分のagent_runsをstage=uploadingで作成し、
    ファイル保存完了時点でprogress_percent=20に更新する。AGENT-01自体の起動はこの関数の
    呼び出し元（agent_orchestrator）が行う。"""
    validate_file_names([f.filename for f in files])

    inquiry_repo = InquiryRepository(session)
    inquiry = await inquiry_repo.add(
        Inquiry(inquiry_code=_generate_inquiry_code(), status="draft")
    )
    await session.flush()

    agent_run = await AgentRunRepository(session).add(
        AgentRun(
            inquiry_id=inquiry.id,
            agent_name="agent01_extraction",
            trigger="new_upload",
            status="running",
            stage="uploading",
            progress_percent=0,
        )
    )
    await session.flush()

    dest_dir = _storage_dir_for(inquiry.id)
    file_repo = InquiryFileRepository(session)
    inquiry_files = []
    for file in files:
        storage_path = await _save_upload(file, dest_dir)
        inquiry_file = await file_repo.add(
            InquiryFile(
                inquiry_id=inquiry.id,
                file_name=file.filename,
                file_type=SUPPORTED_EXTENSIONS[_extension(file.filename)],
                storage_path=storage_path,
            )
        )
        inquiry_files.append(inquiry_file)

    agent_run.progress_percent = 20
    await session.commit()
    return inquiry, inquiry_files, agent_run


async def add_files_to_inquiry(
    session: AsyncSession, inquiry_id: int, files: list[UploadFile]
) -> tuple[list[InquiryFile], AgentRun]:
    """FUNC-01追加アップロード（SCR-05）: 既存引合にファイルを追加する。"""
    validate_file_names([f.filename for f in files])

    agent_run = await AgentRunRepository(session).add(
        AgentRun(
            inquiry_id=inquiry_id,
            agent_name="agent01_extraction",
            trigger="additional_upload",
            status="running",
            stage="uploading",
            progress_percent=0,
        )
    )
    await session.flush()

    dest_dir = _storage_dir_for(inquiry_id)
    file_repo = InquiryFileRepository(session)
    inquiry_files = []
    for file in files:
        storage_path = await _save_upload(file, dest_dir)
        inquiry_file = await file_repo.add(
            InquiryFile(
                inquiry_id=inquiry_id,
                file_name=file.filename,
                file_type=SUPPORTED_EXTENSIONS[_extension(file.filename)],
                storage_path=storage_path,
            )
        )
        inquiry_files.append(inquiry_file)

    agent_run.progress_percent = 20
    await session.commit()
    return inquiry_files, agent_run
