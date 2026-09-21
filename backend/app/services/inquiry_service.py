from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.inquiry import (
    AgentStatusResponse,
    CandidateRead,
    FieldRead,
    FieldUpdateResponse,
    InquiryDetailResponse,
    InquiryHeader,
    InquiryListItem,
    InquiryListResponse,
    ItemRead,
    NoteRead,
    ReviewSummary,
)
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.field_candidate_repository import FieldCandidateRepository
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_item_field_repository import InquiryItemFieldRepository
from app.repositories.inquiry_item_repository import InquiryItemRepository
from app.repositories.inquiry_note_repository import InquiryNoteRepository
from app.repositories.inquiry_repository import InquiryRepository


class InquiryNotFoundError(Exception):
    pass


class AgentStatusNotFoundError(Exception):
    pass


class FieldNotFoundError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


async def list_inquiries(
    session: AsyncSession, status: Literal["draft", "final"] | None = None
) -> InquiryListResponse:
    """GET /inquiries（FUNC-05一覧表示・FUNC-07要確認件数集計、05-api-ipo.md）。

    要確認件数はA項目(inquiry_fields)とB項目(inquiry_item_fields)のstatus=review合算
    （SCR-01一覧の「要確認」列・mockup.htmlの count-link に対応）。
    """
    inquiry_repo = InquiryRepository(session)
    inquiry_field_repo = InquiryFieldRepository(session)
    inquiry_item_field_repo = InquiryItemFieldRepository(session)

    inquiries = await inquiry_repo.list()
    if status is not None:
        inquiries = [i for i in inquiries if i.status == status]

    items = []
    for inquiry in inquiries:
        case_review = await inquiry_field_repo.count_review_by_inquiry(inquiry.id)
        item_review = await inquiry_item_field_repo.count_review_by_inquiry(inquiry.id)
        items.append(
            InquiryListItem(
                id=inquiry.id,
                inquiry_code=inquiry.inquiry_code,
                requester=inquiry.requester,
                project_name=inquiry.project_name,
                status=inquiry.status,
                requested_at=inquiry.requested_at,
                review_count=case_review + item_review,
                updated_at=inquiry.updated_at,
            )
        )

    return InquiryListResponse(items=items, total_count=len(items))


async def get_agent_status(
    session: AsyncSession, inquiry_id: int
) -> AgentStatusResponse:
    """GET /inquiries/{id}/agent-status（agent-plan.md §2: 最新のagent_runs行をそのまま返す）。"""
    inquiry = await InquiryRepository(session).get(inquiry_id)
    if inquiry is None:
        raise InquiryNotFoundError(inquiry_id)

    agent_run = await AgentRunRepository(session).get_latest_by_inquiry(inquiry_id)
    if agent_run is None:
        raise AgentStatusNotFoundError(inquiry_id)

    return AgentStatusResponse(
        stage=agent_run.stage,
        progress_percent=agent_run.progress_percent,
        status=agent_run.status,
        error_message=agent_run.error_message,
    )


async def get_inquiry_detail(
    session: AsyncSession, inquiry_id: int
) -> InquiryDetailResponse:
    """GET /inquiries/{inquiry_id}（FUNC-02〜07の表示、05-api-ipo.md）。

    inquiry_fields/inquiry_item_fields を field_definitions と突き合わせて
    label/display_order を解決する（Scope 1は固定スキーマのため専用エンドポイントは設けない）。
    """
    inquiry = await InquiryRepository(session).get(inquiry_id)
    if inquiry is None:
        raise InquiryNotFoundError(inquiry_id)

    field_defs = {f.id: f for f in await FieldDefinitionRepository(session).list()}
    candidate_repo = FieldCandidateRepository(session)

    async def _to_field_read(row, *, is_item: bool) -> FieldRead:
        definition = field_defs[row.field_definition_id]
        candidates = (
            await candidate_repo.list_by_inquiry_item_field(row.id)
            if is_item
            else await candidate_repo.list_by_inquiry_field(row.id)
        )
        return FieldRead(
            field_id=definition.field_id,
            label=definition.label,
            display_order=definition.display_order,
            value=row.value,
            status=row.status,
            reason_type=row.reason_type,
            is_web_supplemented=row.is_web_supplemented,
            confirmed_by=row.confirmed_by,
            candidates=[CandidateRead.model_validate(c) for c in candidates],
        )

    case_rows = await InquiryFieldRepository(session).list_by_inquiry(inquiry_id)
    case_fields = [await _to_field_read(row, is_item=False) for row in case_rows]
    case_fields.sort(key=lambda f: f.display_order)

    notes = await InquiryNoteRepository(session).list_by_inquiry(inquiry_id)
    case_notes = [NoteRead.model_validate(n) for n in notes if n.scope == "case"]

    item_field_repo = InquiryItemFieldRepository(session)
    items: list[ItemRead] = []
    for item in await InquiryItemRepository(session).list_by_inquiry(inquiry_id):
        item_rows = await item_field_repo.list_by_inquiry_item(item.id)
        item_fields = [await _to_field_read(row, is_item=True) for row in item_rows]
        item_fields.sort(key=lambda f: f.display_order)
        items.append(
            ItemRead(
                id=item.id,
                item_no=item.item_no,
                fields=item_fields,
                notes=[
                    NoteRead.model_validate(n)
                    for n in notes
                    if n.scope == "item" and n.inquiry_item_id == item.id
                ],
            )
        )

    all_fields = case_fields + [f for item in items for f in item.fields]
    review_summary = ReviewSummary(
        review_count=sum(1 for f in all_fields if f.status == "review"),
        web_supplemented_count=sum(1 for f in all_fields if f.is_web_supplemented),
    )

    return InquiryDetailResponse(
        inquiry=InquiryHeader.model_validate(inquiry),
        case_fields=case_fields,
        items=items,
        case_notes=case_notes,
        review_summary=review_summary,
    )


async def _apply_field_update(
    session: AsyncSession,
    row,
    candidates: list,
    *,
    field_id: str,
    value: str,
    selected_candidate_id: int | None,
) -> FieldUpdateResponse:
    """FUNC-08 担当者による確認・修正の更新ロジック（05-api-ipo.md の5ステップ）。

    (1) selected_candidate_id指定時はその候補のis_selected=true、他はfalse
    (2) value を更新
    (3) valueが空文字列なら status=review / reason_type=missing、それ以外は ok / NULL
    (4) confirmed_by='user'
    (5) is_web_supplemented を再計算（選んだ候補がsource_type='web'のときのみtrue）
    """
    selected_candidate = None
    if selected_candidate_id is not None:
        for candidate in candidates:
            is_selected = candidate.id == selected_candidate_id
            candidate.is_selected = is_selected
            if is_selected:
                selected_candidate = candidate

    row.value = value
    if value == "":
        row.status = "review"
        row.reason_type = "missing"
    else:
        row.status = "ok"
        row.reason_type = None
    row.confirmed_by = "user"
    row.is_web_supplemented = (
        selected_candidate is not None and selected_candidate.source_type == "web"
    )

    await session.commit()

    return FieldUpdateResponse(
        field_id=field_id,
        value=row.value,
        status=row.status,
        reason_type=row.reason_type,
        confirmed_by="user",
        is_web_supplemented=row.is_web_supplemented,
    )


async def update_case_field(
    session: AsyncSession,
    inquiry_id: int,
    field_id: str,
    *,
    value: str,
    selected_candidate_id: int | None = None,
) -> FieldUpdateResponse:
    """PATCH /inquiries/{inquiry_id}/fields/{field_id}（A項目）。"""
    inquiry = await InquiryRepository(session).get(inquiry_id)
    if inquiry is None:
        raise InquiryNotFoundError(inquiry_id)

    definition = await FieldDefinitionRepository(session).get_by_field_id(field_id)
    if definition is None or definition.scope != "case":
        raise FieldNotFoundError(field_id)

    row = await InquiryFieldRepository(session).get_by_inquiry_and_field(
        inquiry_id, definition.id
    )
    if row is None:
        raise FieldNotFoundError(field_id)

    candidates = await FieldCandidateRepository(session).list_by_inquiry_field(row.id)
    return await _apply_field_update(
        session,
        row,
        candidates,
        field_id=field_id,
        value=value,
        selected_candidate_id=selected_candidate_id,
    )


async def update_item_field(
    session: AsyncSession,
    inquiry_id: int,
    item_id: int,
    field_id: str,
    *,
    value: str,
    selected_candidate_id: int | None = None,
) -> FieldUpdateResponse:
    """PATCH /inquiries/{inquiry_id}/items/{item_id}/fields/{field_id}（B項目）。"""
    inquiry = await InquiryRepository(session).get(inquiry_id)
    if inquiry is None:
        raise InquiryNotFoundError(inquiry_id)

    item = await InquiryItemRepository(session).get(item_id)
    if item is None or item.inquiry_id != inquiry_id:
        raise ItemNotFoundError(item_id)

    definition = await FieldDefinitionRepository(session).get_by_field_id(field_id)
    if definition is None or definition.scope != "item":
        raise FieldNotFoundError(field_id)

    row = await InquiryItemFieldRepository(session).get_by_item_and_field(
        item_id, definition.id
    )
    if row is None:
        raise FieldNotFoundError(field_id)

    candidates = await FieldCandidateRepository(session).list_by_inquiry_item_field(
        row.id
    )
    return await _apply_field_update(
        session,
        row,
        candidates,
        field_id=field_id,
        value=value,
        selected_candidate_id=selected_candidate_id,
    )
