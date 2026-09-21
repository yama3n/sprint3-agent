from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.inquiry import InquiryListResponse
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.services import inquiry_service

router = APIRouter(prefix="/inquiries", tags=["Inquiries"])


@router.get("", response_model=InquiryListResponse)
async def list_inquiries(
    status: Literal["draft", "final"] | None = None,
    session: AsyncSession = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> InquiryListResponse:
    return await inquiry_service.list_inquiries(session, status=status)
