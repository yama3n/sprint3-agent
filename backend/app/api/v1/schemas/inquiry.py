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


class UploadResponse(BaseModel):
    """POST /inquiries・POST /inquiries/{id}/files のレスポンス（05-api-ipo.md）。"""

    inquiry_id: int
    status: Literal["draft"] = "draft"
    agent_run_id: int


AgentStage = Literal[
    "uploading",
    "extracting",
    "structuring",
    "reviewing",
    "completed",
    "failed",
    "stopped",
]


class AgentStatusResponse(BaseModel):
    """GET /inquiries/{id}/agent-status のレスポンス（05-api-ipo.md）。
    対象引合のagent_runsのうち最も新しい行のstage/progress_percent/statusをそのまま返す。"""

    stage: AgentStage
    progress_percent: int
    status: str
    error_message: str | None = None


# --- GET /inquiries/{id}（SCR-03 引合詳細・SCR-04 Inspector）---

ReasonType = Literal[
    "missing", "conflict", "ambiguous", "multiple_candidates", "parse_error"
]
FieldStatus = Literal["ok", "review"]
SourceType = Literal["pdf", "excel", "eml", "web"]


class CandidateRead(BaseModel):
    """候補値と出典（FUNC-06 抽出根拠の提示。SCR-04 Inspectorの候補比較・出典プレビュー用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    value: str
    source_type: SourceType
    source_file: str | None = None
    source_location: str | None = None
    quoted_text: str | None = None
    web_url: str | None = None
    web_source_name: str | None = None
    web_referenced_at: datetime.datetime | None = None
    is_explicit_correction: bool = False
    superseded_value: str | None = None
    is_selected: bool = False


class FieldRead(BaseModel):
    """A項目/B項目1件分（FUNC-07 ステータス・FUNC-06 出典）。"""

    field_id: str
    label: str
    display_order: int
    value: str | None = None
    status: FieldStatus
    reason_type: ReasonType | None = None
    is_web_supplemented: bool = False
    confirmed_by: Literal["ai", "web", "user"] | None = None
    candidates: list[CandidateRead] = []


class NoteRead(BaseModel):
    """その他特記事項／その他条件（拡張項目。{項目内容, 出典}の配列）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    source_type: SourceType | None = None
    source_file: str | None = None
    source_location: str | None = None


class ItemRead(BaseModel):
    """品目1件分（B項目8つ + 品目固有のその他条件）。"""

    id: int
    item_no: int
    fields: list[FieldRead]
    notes: list[NoteRead] = []


class InquiryHeader(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inquiry_code: str
    requester: str | None = None
    project_name: str | None = None
    status: Literal["draft", "final"]
    requested_at: datetime.datetime | None = None
    updated_at: datetime.datetime


class ReviewSummary(BaseModel):
    review_count: int
    web_supplemented_count: int


class InquiryDetailResponse(BaseModel):
    """GET /inquiries/{inquiry_id} のレスポンス（05-api-ipo.md）。"""

    inquiry: InquiryHeader
    case_fields: list[FieldRead]
    items: list[ItemRead]
    case_notes: list[NoteRead]
    review_summary: ReviewSummary


# --- PATCH .../fields/{field_id}（FUNC-08 担当者による確認・修正 / SCR-04）---


class FieldUpdateRequest(BaseModel):
    """05-api-ipo.md: value は必須（空文字列も許容）。候補選択時のみ selected_candidate_id。"""

    value: str
    selected_candidate_id: int | None = None


class FieldUpdateResponse(BaseModel):
    field_id: str
    value: str
    status: FieldStatus
    reason_type: ReasonType | None = None
    confirmed_by: Literal["user"] = "user"
    is_web_supplemented: bool


# --- FUNC-09 成果物確定 / FUNC-05 成果物生成 ---


class ConfirmResponse(BaseModel):
    """POST /inquiries/{id}/confirm のレスポンス（05-api-ipo.md）。"""

    inquiry_id: int
    status: Literal["final"] = "final"
    confirmed_at: datetime.datetime


class ExportRequest(BaseModel):
    """Scope 1 で有効なのは excel のみ（word/pdf は Scope 2。400 UNSUPPORTED_FORMAT）。"""

    format: Literal["excel", "word", "pdf"] = "excel"


class ExportResponse(BaseModel):
    export_id: int
    file_name: str
