import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class InquiryBase(BaseModel):
    inquiry_code: str
    requester: str | None = None
    project_name: str | None = None
    status: Literal["draft", "final"] = "draft"


class InquiryCreate(InquiryBase):
    created_by_user_id: int | None = None


class InquiryRead(InquiryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int | None = None
    requested_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class InquiryListItem(BaseModel):
    """GET /inquiries の1行分（05-api-ipo.md）。SCR-01一覧テーブルに対応する。"""

    id: int
    inquiry_code: str
    requester: str | None = None
    project_name: str | None = None
    status: Literal["draft", "final"]
    requested_at: datetime.datetime | None = None
    review_count: int
    updated_at: datetime.datetime


class InquiryListResponse(BaseModel):
    items: list[InquiryListItem]
    total_count: int
