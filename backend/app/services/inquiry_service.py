from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.inquiry import (
    AgentStatusResponse,
    InquiryListItem,
    InquiryListResponse,
)
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_item_field_repository import InquiryItemFieldRepository
from app.repositories.inquiry_repository import InquiryRepository


class InquiryNotFoundError(Exception):
    pass


class AgentStatusNotFoundError(Exception):
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
