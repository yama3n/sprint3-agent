from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.inquiry_deletion_repository import InquiryDeletionRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.services.inquiry_service import InquiryNotFoundError


def _remove_managed_files(paths: list[str]) -> None:
    """DBに記録されたうち、管理対象STORAGE_DIR配下のファイルだけを削除する。"""
    storage_root = Path(settings.STORAGE_DIR).resolve()
    for raw_path in paths:
        path = Path(raw_path).resolve()
        if path.is_relative_to(storage_root) and path.is_file():
            path.unlink()


async def delete_inquiry(session: AsyncSession, inquiry_id: int) -> None:
    if await InquiryRepository(session).get(inquiry_id) is None:
        raise InquiryNotFoundError(inquiry_id)

    paths = await InquiryDeletionRepository(session).delete(inquiry_id)
    await session.commit()
    _remove_managed_files(paths)
