import json
import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent02 import state
from app.agent.agent02.tools import (
    classify_status,
    compare_and_merge_candidates,
    load_existing_inquiry,
    save_structured_result,
    web_search_company_info,
)
from app.core.db import AsyncSessionLocal
from app.models.agent_run import AgentRun
from app.models.field import FieldCandidate, InquiryField, InquiryItemField
from app.models.inquiry import Inquiry, InquiryItem, InquiryNote
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_repository import InquiryRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def created_inquiry_ids():
    ids: list[int] = []
    yield ids
    if not ids:
        return
    async with AsyncSessionLocal() as cleanup_session:
        field_ids_res = await cleanup_session.execute(
            select(InquiryField.id).where(InquiryField.inquiry_id.in_(ids))
        )
        field_ids = [r[0] for r in field_ids_res.fetchall()]
        item_ids_res = await cleanup_session.execute(
            select(InquiryItem.id).where(InquiryItem.inquiry_id.in_(ids))
        )
        item_ids = [r[0] for r in item_ids_res.fetchall()]
        item_field_ids_res = await cleanup_session.execute(
            select(InquiryItemField.id).where(
                InquiryItemField.inquiry_item_id.in_(item_ids)
            )
        )
        item_field_ids = [r[0] for r in item_field_ids_res.fetchall()]

        await cleanup_session.execute(
            delete(FieldCandidate).where(FieldCandidate.inquiry_field_id.in_(field_ids))
        )
        await cleanup_session.execute(
            delete(FieldCandidate).where(
                FieldCandidate.inquiry_item_field_id.in_(item_field_ids)
            )
        )
        await cleanup_session.execute(
            delete(InquiryItemField).where(InquiryItemField.id.in_(item_field_ids))
        )
        await cleanup_session.execute(
            delete(InquiryNote).where(InquiryNote.inquiry_id.in_(ids))
        )
        await cleanup_session.execute(
            delete(InquiryItem).where(InquiryItem.id.in_(item_ids))
        )
        await cleanup_session.execute(
            delete(InquiryField).where(InquiryField.id.in_(field_ids))
        )
        await cleanup_session.execute(
            delete(AgentRun).where(AgentRun.inquiry_id.in_(ids))
        )
        await cleanup_session.execute(delete(Inquiry).where(Inquiry.id.in_(ids)))
        await cleanup_session.commit()
    for inquiry_id in ids:
        state.clear_state(inquiry_id)


async def _make_inquiry(
    db_session: AsyncSession, created_inquiry_ids: list[int]
) -> int:
    inquiry = await InquiryRepository(db_session).add(
        Inquiry(inquiry_code=f"INQ-TEST-AGENT02-{uuid.uuid4().hex[:8]}", status="draft")
    )
    await db_session.flush()
    created_inquiry_ids.append(inquiry.id)
    agent_run = await AgentRunRepository(db_session).add(
        AgentRun(
            inquiry_id=inquiry.id,
            agent_name="agent02_verification",
            trigger="new_upload",
            status="running",
            stage="structuring",
        )
    )
    await db_session.commit()
    return inquiry.id, agent_run.id


def _minimal_case_fields_payload(inquiry_id: int, requester_value: str) -> dict:
    from app.agent.agent01.schema import CASE_FIELD_IDS

    fields = [
        {
            "field_id": "requester",
            "value": requester_value,
            "candidates": [
                {
                    "value": requester_value,
                    "source_type": "excel",
                    "source_file": "a.xlsx",
                    "source_location": "A1",
                    "quoted_text": requester_value,
                }
            ],
        }
    ]
    for field_id in CASE_FIELD_IDS:
        if field_id == "requester":
            continue
        fields.append({"field_id": field_id, "value": None, "candidates": []})
    return {"inquiry_id": inquiry_id, "fields": fields}


def _minimal_item_fields_payload(inquiry_id: int, item_no: int) -> dict:
    from app.agent.agent01.schema import ITEM_FIELD_IDS

    fields = [
        {"field_id": field_id, "item_no": item_no, "value": None, "candidates": []}
        for field_id in ITEM_FIELD_IDS
    ]
    return {"inquiry_id": inquiry_id, "fields": fields}


def _classify_all_missing(inquiry_id: int, item_no: int) -> dict:
    from app.agent.agent01.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS

    decisions = [
        {"field_id": "requester", "status": "ok"},
    ]
    decisions += [
        {"field_id": fid, "status": "review", "reason_type": "missing"}
        for fid in CASE_FIELD_IDS
        if fid != "requester"
    ]
    decisions += [
        {
            "field_id": fid,
            "item_no": item_no,
            "status": "review",
            "reason_type": "missing",
        }
        for fid in ITEM_FIELD_IDS
    ]
    return {"inquiry_id": inquiry_id, "decisions": decisions}


async def test_pipeline_saves_structured_result_for_new_upload(
    db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id, agent_run_id = await _make_inquiry(db_session, created_inquiry_ids)

    merge_result = await compare_and_merge_candidates.handler(
        _minimal_case_fields_payload(inquiry_id, "東西石油開発株式会社")
    )
    assert merge_result.get("is_error") is not True
    item_merge = await compare_and_merge_candidates.handler(
        _minimal_item_fields_payload(inquiry_id, 1)
    )
    assert item_merge.get("is_error") is not True

    agent_state = state.get_state(inquiry_id)
    agent_state.fields[("inquiry_date", None)].value = "2026年7月10日"
    agent_state.case_notes = [
        {
            "content": "輸送条件は別途協議",
            "source_type": "pdf",
            "source_file": "a.pdf",
            "source_location": "1ページ",
        }
    ]
    agent_state.item_notes = {
        1: [
            {
                "content": "品目注記",
                "source_type": "pdf",
                "source_file": "a.pdf",
                "source_location": "2ページ",
            }
        ]
    }

    classify_result = await classify_status.handler(
        _classify_all_missing(inquiry_id, 1)
    )
    assert classify_result.get("is_error") is not True

    save_result = await save_structured_result.handler(
        {"inquiry_id": inquiry_id, "agent_run_id": agent_run_id}
    )
    assert save_result.get("is_error") is not True
    payload = json.loads(save_result["content"][0]["text"])
    assert payload["saved"] is True

    async with AsyncSessionLocal() as verify_session:
        field_def = (
            await FieldDefinitionRepository(verify_session).list_by_scope("case")
        )[0]
        row = await InquiryFieldRepository(verify_session).get_by_inquiry_and_field(
            inquiry_id, field_def.id
        )
        assert row is not None
        assert row.value == "東西石油開発株式会社"
        assert row.status == "ok"
        assert row.confirmed_by == "ai"

        run = await verify_session.get(AgentRun, agent_run_id)
        assert run.status == "succeeded"
        assert run.progress_percent == 100

        inquiry = await InquiryRepository(verify_session).get(inquiry_id)
        assert inquiry.requester == "東西石油開発株式会社"
        assert inquiry.requested_at.isoformat() == "2026-07-10T00:00:00+00:00"

        notes = (
            await verify_session.execute(
                select(InquiryNote).where(InquiryNote.inquiry_id == inquiry_id)
            )
        ).scalars().all()
        assert {note.content for note in notes} == {"輸送条件は別途協議", "品目注記"}


async def test_confirmed_by_user_value_is_protected_on_conflicting_reupload(
    db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    """TEST-14相当: 担当者確定済み値は新資料の候補と異なっても自動上書きされない。"""
    inquiry_id, agent_run_id = await _make_inquiry(db_session, created_inquiry_ids)

    field_def = (await FieldDefinitionRepository(db_session).list_by_scope("case"))[0]
    await InquiryFieldRepository(db_session).add(
        InquiryField(
            inquiry_id=inquiry_id,
            field_definition_id=field_def.id,
            value="320本",
            status="ok",
            confirmed_by="user",
        )
    )
    await db_session.commit()

    await load_existing_inquiry.handler({"inquiry_id": inquiry_id})

    payload = _minimal_case_fields_payload(inquiry_id, "320本")
    # 1件目のfieldは動的に選んだfield_def.field_idに合わせる必要があるため差し替える
    payload["fields"][0] = {
        "field_id": field_def.field_id,
        "value": "280本",
        "candidates": [
            {
                "value": "280本",
                "source_type": "excel",
                "source_file": "new.xlsx",
                "source_location": "A1",
                "quoted_text": "280本",
            }
        ],
    }
    await compare_and_merge_candidates.handler(payload)
    await compare_and_merge_candidates.handler(
        _minimal_item_fields_payload(inquiry_id, 1)
    )

    decisions = _classify_all_missing(inquiry_id, 1)
    decisions["decisions"][0] = {"field_id": field_def.field_id, "status": "ok"}
    await classify_status.handler(decisions)

    save_result = await save_structured_result.handler(
        {"inquiry_id": inquiry_id, "agent_run_id": agent_run_id}
    )
    assert save_result.get("is_error") is not True

    async with AsyncSessionLocal() as verify_session:
        row = await InquiryFieldRepository(verify_session).get_by_inquiry_and_field(
            inquiry_id, field_def.id
        )
        assert row.value == "320本"  # 上書きされていない
        assert row.status == "review"
        assert row.reason_type == "conflict"
        assert row.confirmed_by == "user"

        candidates = await verify_session.execute(
            select(FieldCandidate).where(FieldCandidate.inquiry_field_id == row.id)
        )
        values = {c.value for c in candidates.scalars().all()}
        assert "280本" in values


async def test_web_search_company_info_rejects_disallowed_field(
    db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id, _ = await _make_inquiry(db_session, created_inquiry_ids)
    await compare_and_merge_candidates.handler(
        {
            "inquiry_id": inquiry_id,
            "fields": [
                {"field_id": "desired_delivery", "value": None, "candidates": []}
            ],
        }
    )
    await classify_status.handler(
        {
            "inquiry_id": inquiry_id,
            "decisions": [
                {
                    "field_id": "desired_delivery",
                    "status": "review",
                    "reason_type": "missing",
                }
            ],
        }
    )

    response = await web_search_company_info.handler(
        {
            "inquiry_id": inquiry_id,
            "field_id": "desired_delivery",
            "value": "2027年3月",
            "url": "https://example.com",
            "source_name": "Example",
        }
    )
    assert response.get("is_error") is True


async def test_web_search_company_info_updates_missing_field_to_ok(
    db_session: AsyncSession, created_inquiry_ids: list[int]
) -> None:
    inquiry_id, _ = await _make_inquiry(db_session, created_inquiry_ids)
    await compare_and_merge_candidates.handler(
        {
            "inquiry_id": inquiry_id,
            "fields": [{"field_id": "requester", "value": None, "candidates": []}],
        }
    )
    await classify_status.handler(
        {
            "inquiry_id": inquiry_id,
            "decisions": [
                {"field_id": "requester", "status": "review", "reason_type": "missing"}
            ],
        }
    )

    response = await web_search_company_info.handler(
        {
            "inquiry_id": inquiry_id,
            "field_id": "requester",
            "value": "東西石油開発株式会社",
            "url": "https://tozai-sekiyu.example.com",
            "source_name": "東西石油開発 公式サイト",
        }
    )
    assert response.get("is_error") is not True
    field_state = state.get_state(inquiry_id).fields[("requester", None)]
    assert field_state.status == "ok"
    assert field_state.is_web_supplemented is True
