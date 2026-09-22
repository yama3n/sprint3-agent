"""AGENT-02のツール群（Claude Agent SDK @tool）。agent-plan.md §4 Part2のツール一覧と1対1。

- load_existing_inquiry: 決定論的なDB読み取り（追加アップロード時のみ使用）。
- compare_and_merge_candidates/evaluate_explicit_correction/classify_status: AGENT-02自身
  （呼び出し元のClaude）が判断した統合結果・訂正評価・ステータス分類を受け取り、固定項目
  スキーマに沿って検証・集約する（validation.py）。判断そのものはここでは行わない
  （agent-development.md追加要件: if/elseでAGENT-02の意味判断を代替しない）。
- web_search_company_info: 組み込みWebSearchツール（guardrails.pyのPreToolUseフックでFUNC-04の
  対象外語をブロック）でAGENT-02自身が検索した結果を、許可されたfield_idのみ登録する。
- save_structured_result: 統合結果を完了条件チェックのうえDBへ永続化する。追加アップロード時、
  confirmed_by=userの既存確定値を新候補で自動上書きしない（4章ルール）ことを構造的に強制する。
"""

import json
import re
from datetime import UTC, datetime
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.agent.agent02 import state, validation
from app.agent.agent02.schema import WEB_SUPPLEMENT_ALLOWED_CASE_FIELD_IDS
from app.agent.agent02.tool_schemas import (
    CLASSIFY_STATUS_SCHEMA,
    COMPARE_AND_MERGE_CANDIDATES_SCHEMA,
    EVALUATE_EXPLICIT_CORRECTION_SCHEMA,
    LOAD_EXISTING_INQUIRY_SCHEMA,
    SAVE_STRUCTURED_RESULT_SCHEMA,
    WEB_SEARCH_COMPANY_INFO_SCHEMA,
)
from app.agent.agent02.state import FieldState
from app.core.db import AsyncSessionLocal
from app.models.field import FieldCandidate, InquiryField, InquiryItemField
from app.models.inquiry import InquiryItem, InquiryNote
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.field_candidate_repository import FieldCandidateRepository
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_item_field_repository import InquiryItemFieldRepository
from app.repositories.inquiry_item_repository import InquiryItemRepository
from app.repositories.inquiry_note_repository import InquiryNoteRepository
from app.repositories.inquiry_repository import InquiryRepository


def _error(message: str) -> dict[str, Any]:
    return {
        "content": [
            {"type": "text", "text": json.dumps({"error": message}, ensure_ascii=False)}
        ],
        "is_error": True,
    }


def _ok(payload: dict) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]
    }


@tool(
    "load_existing_inquiry",
    "追加アップロード時に、対象引合の既存の値・状態・確定主体(confirmed_by)・候補・出典を取得する。"
    "新規アップロードの場合は呼ばなくてよい。",
    LOAD_EXISTING_INQUIRY_SCHEMA,
)
async def load_existing_inquiry(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    async with AsyncSessionLocal() as session:
        inquiry = await InquiryRepository(session).get(inquiry_id)
        if inquiry is None:
            return _error("INQUIRY_NOT_FOUND")
        case_fields = await InquiryFieldRepository(session).list_by_inquiry(inquiry_id)
        field_def_repo = FieldDefinitionRepository(session)
        case_field_defs = {f.id: f.field_id for f in await field_def_repo.list()}

        existing_case = {}
        for f in case_fields:
            existing_case[case_field_defs.get(f.field_definition_id, "?")] = {
                "value": f.value,
                "status": f.status,
                "reason_type": f.reason_type,
                "confirmed_by": f.confirmed_by,
                "is_web_supplemented": f.is_web_supplemented,
            }

        items = await InquiryItemRepository(session).list_by_inquiry(inquiry_id)
        existing_items: dict[str, dict] = {}
        item_field_repo = InquiryItemFieldRepository(session)
        for item in items:
            item_fields = await item_field_repo.list_by_inquiry_item(item.id)
            existing_items[str(item.item_no)] = {
                case_field_defs.get(f.field_definition_id, "?"): {
                    "value": f.value,
                    "status": f.status,
                    "reason_type": f.reason_type,
                    "confirmed_by": f.confirmed_by,
                    "is_web_supplemented": f.is_web_supplemented,
                }
                for f in item_fields
            }

    payload = {
        "inquiry_id": inquiry_id,
        "status": inquiry.status,
        "case_fields": existing_case,
        "items": existing_items,
    }
    state.get_state(inquiry_id).existing = payload
    return _ok(payload)


@tool(
    "compare_and_merge_candidates",
    "同一項目について複数資料の候補値を比較し、一致するものは統合、割れているものは統合せず"
    "候補のまま保持した結果を登録する。判断はあなた自身が行うこと。",
    COMPARE_AND_MERGE_CANDIDATES_SCHEMA,
)
async def compare_and_merge_candidates(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    agent_state = state.get_state(inquiry_id)
    registered = []
    try:
        for entry in args["fields"]:
            field_id = entry["field_id"]
            item_no = entry.get("item_no")
            validation.validate_field_ref(field_id, item_no)
            for candidate in entry["candidates"]:
                validation.validate_candidate(candidate)
            key = (field_id, item_no)
            agent_state.fields[key] = FieldState(
                field_id=field_id,
                item_no=item_no,
                value=entry.get("value"),
                candidates=entry["candidates"],
            )
            registered.append({"field_id": field_id, "item_no": item_no})
    except ValueError as e:
        return _error(str(e))
    return _ok({"registered": registered})


@tool(
    "evaluate_explicit_correction",
    "candidateのcorrection_hintをもとに、明示的な訂正意図が読み取れる項目について採用値を登録する。"
    "compare_and_merge_candidates呼び出し後に、訂正表現のある項目のみ渡すこと。",
    EVALUATE_EXPLICIT_CORRECTION_SCHEMA,
)
async def evaluate_explicit_correction(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    agent_state = state.get_state(inquiry_id)
    updated = []
    for correction in args["corrections"]:
        field_id = correction["field_id"]
        item_no = correction.get("item_no")
        key = (field_id, item_no)
        if key not in agent_state.fields:
            return _error(
                f"{field_id}: compare_and_merge_candidatesが先に呼び出されていません"
            )
        field_state = agent_state.fields[key]
        field_state.value = correction["adopted_value"]
        for candidate in field_state.candidates:
            if candidate.get("value") == correction["adopted_value"]:
                candidate["is_explicit_correction"] = True
                if "superseded_value" in correction:
                    candidate["superseded_value"] = correction["superseded_value"]
        updated.append({"field_id": field_id, "item_no": item_no})
    return _ok({"updated": updated})


@tool(
    "classify_status",
    "各項目に内部ステータス（確認不要=ok または 要確認=review〔理由付き〕）を付与する。"
    "compare_and_merge_candidates（・evaluate_explicit_correction）の後に、対象の全項目分呼ぶこと。",
    CLASSIFY_STATUS_SCHEMA,
)
async def classify_status(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    agent_state = state.get_state(inquiry_id)
    # 最初の分類処理に入った時点を「要確認項目整理中」として公開する。
    # Claudeの意味判断は変更せず、決定論的な進捗表示だけを更新する。
    async with AsyncSessionLocal() as session:
        latest_run = await AgentRunRepository(session).get_latest_by_inquiry(inquiry_id)
        if latest_run is not None and latest_run.status == "running":
            latest_run.stage = "reviewing"
            latest_run.progress_percent = max(latest_run.progress_percent, 80)
            await session.commit()
    updated = []
    for decision in args["decisions"]:
        field_id = decision["field_id"]
        item_no = decision.get("item_no")
        key = (field_id, item_no)
        if key not in agent_state.fields:
            return _error(
                f"{field_id}: compare_and_merge_candidatesが先に呼び出されていません"
            )
        field_state = agent_state.fields[key]
        field_state.status = decision["status"]
        field_state.reason_type = (
            decision.get("reason_type") if decision["status"] == "review" else None
        )
        updated.append(
            {"field_id": field_id, "item_no": item_no, "status": field_state.status}
        )
    return _ok({"updated": updated})


@tool(
    "web_search_company_info",
    "status=missingの項目のうち、公開情報で客観的に確認可能な企業情報・市況に限り、組み込みの"
    "WebSearchツールで調べた結果を登録する。対象を一意に特定できた場合のみ呼ぶこと"
    "（同名候補が複数・情報源不明瞭な場合は呼ばず要確認のまま保持する）。",
    WEB_SEARCH_COMPANY_INFO_SCHEMA,
)
async def web_search_company_info(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    field_id = args["field_id"]
    item_no = args.get("item_no")

    if item_no is not None or field_id not in WEB_SUPPLEMENT_ALLOWED_CASE_FIELD_IDS:
        return _error(
            f"{field_id}はWeb補完の対象外です（許可対象: {sorted(WEB_SUPPLEMENT_ALLOWED_CASE_FIELD_IDS)}）"
        )

    agent_state = state.get_state(inquiry_id)
    key = (field_id, None)
    field_state = agent_state.fields.get(key)
    if field_state is None or field_state.reason_type != "missing":
        return _error(
            f"{field_id}はclassify_statusでreason_type=missingと判定されていません"
        )

    field_state.value = args["value"]
    field_state.status = "ok"
    field_state.reason_type = None
    field_state.is_web_supplemented = True
    field_state.candidates.append(
        {
            "value": args["value"],
            "source_type": "web",
            "web_url": args["url"],
            "web_source_name": args["source_name"],
            "web_referenced_at": args.get("referenced_at")
            or datetime.now(UTC).isoformat(),
            "is_selected": True,
        }
    )
    return _ok(
        {"field_id": field_id, "value": field_state.value, "is_web_supplemented": True}
    )


def _resolve_confirmed_by(field_state: FieldState) -> str | None:
    if field_state.status != "ok":
        return None
    if any(c.get("source_type") == "web" for c in field_state.candidates):
        return "web"
    return "ai"


def _parse_inquiry_date(value: str | None) -> datetime | None:
    """A項目の引合日を一覧・詳細ヘッダー用datetimeへ正規化する。"""
    if not value:
        return None
    normalized = value.strip()
    japanese = re.fullmatch(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", normalized)
    if japanese:
        year, month, day = map(int, japanese.groups())
        return datetime(year, month, day, tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


async def _persist_field(
    session,
    field_def_id_by_field_id: dict[str, int],
    field_state: FieldState,
    *,
    inquiry_id: int | None = None,
    inquiry_item_id: int | None = None,
    existing_case_or_item: dict | None,
) -> None:
    field_definition_id = field_def_id_by_field_id[field_state.field_id]
    existing_entry = (existing_case_or_item or {}).get(field_state.field_id)

    value = field_state.value
    status = field_state.status
    reason_type = field_state.reason_type
    confirmed_by = _resolve_confirmed_by(field_state)
    is_web_supplemented = field_state.is_web_supplemented

    # 追加アップロード時のユーザー確定値保護（02-requirement.md 4章ルール）。
    # AGENT-02自身の判断を信頼するだけでなく、ここで構造的に強制する。
    if existing_entry and existing_entry.get("confirmed_by") == "user":
        if existing_entry.get("value") == value:
            status, reason_type, confirmed_by = "ok", None, "user"
        else:
            value = existing_entry["value"]
            status, reason_type, confirmed_by = "review", "conflict", "user"
            is_web_supplemented = existing_entry.get("is_web_supplemented", False)

    if inquiry_item_id is not None:
        repo = InquiryItemFieldRepository(session)
        row = await repo.get_by_item_and_field(inquiry_item_id, field_definition_id)
        if row is None:
            row = InquiryItemField(
                inquiry_item_id=inquiry_item_id, field_definition_id=field_definition_id
            )
            session.add(row)
            await session.flush()
    else:
        repo = InquiryFieldRepository(session)
        row = await repo.get_by_inquiry_and_field(inquiry_id, field_definition_id)
        if row is None:
            row = InquiryField(
                inquiry_id=inquiry_id, field_definition_id=field_definition_id
            )
            session.add(row)
            await session.flush()

    row.value = value
    row.status = status
    row.reason_type = reason_type
    row.confirmed_by = confirmed_by
    row.is_web_supplemented = is_web_supplemented

    candidate_repo = FieldCandidateRepository(session)
    for candidate in field_state.candidates:
        kwargs: dict[str, Any] = {
            "value": candidate["value"],
            "source_type": candidate["source_type"],
            "source_file": candidate.get("source_file"),
            "source_location": candidate.get("source_location"),
            "quoted_text": candidate.get("quoted_text"),
            "web_url": candidate.get("web_url"),
            "web_source_name": candidate.get("web_source_name"),
            "web_referenced_at": _parse_iso_datetime(
                candidate.get("web_referenced_at")
            ),
            "is_explicit_correction": candidate.get("is_explicit_correction", False),
            "superseded_value": candidate.get("superseded_value"),
            # 要確認項目では候補の一方を自動採用した表示にしない。
            "is_selected": status == "ok" and candidate.get("value") == value,
        }
        if inquiry_item_id is not None:
            kwargs["inquiry_item_field_id"] = row.id
        else:
            kwargs["inquiry_field_id"] = row.id
        await candidate_repo.add(FieldCandidate(**kwargs))


@tool(
    "save_structured_result",
    "検証・補完済みの結果を、引合単位の構造化JSON（確認中状態）として保存する。"
    "compare_and_merge_candidates・classify_statusを全項目分呼んだ後に呼ぶこと。",
    SAVE_STRUCTURED_RESULT_SCHEMA,
)
async def save_structured_result(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    agent_run_id = args["agent_run_id"]
    agent_state = state.get_state(inquiry_id)

    item_nos = sorted(
        {item_no for (_, item_no) in agent_state.fields if item_no is not None}
    )
    errors = validation.validate_completion(agent_state, item_nos)
    if errors:
        return _error("完了条件を満たしていません: " + " / ".join(errors))

    async with AsyncSessionLocal() as session:
        inquiry = await InquiryRepository(session).get(inquiry_id)
        if inquiry is None:
            return _error("INQUIRY_NOT_FOUND")
        field_def_repo = FieldDefinitionRepository(session)
        field_def_id_by_field_id = {
            f.field_id: f.id for f in await field_def_repo.list()
        }

        existing = agent_state.existing or {}
        existing_case = existing.get("case_fields", {})
        existing_items = existing.get("items", {})

        for (field_id, item_no), field_state in agent_state.fields.items():
            if item_no is None:
                await _persist_field(
                    session,
                    field_def_id_by_field_id,
                    field_state,
                    inquiry_id=inquiry_id,
                    existing_case_or_item=existing_case,
                )

        # inquiriesの2列は一覧表示用キャッシュ。正本であるA項目から一方向に同期する。
        requester = agent_state.fields.get(("requester", None))
        project_name = agent_state.fields.get(("project_name", None))
        if requester is not None:
            inquiry.requester = requester.value
        if project_name is not None:
            inquiry.project_name = project_name.value
        inquiry_date = agent_state.fields.get(("inquiry_date", None))
        if inquiry_date is not None:
            inquiry.requested_at = _parse_inquiry_date(inquiry_date.value)

        item_repo = InquiryItemRepository(session)
        existing_db_items = {
            item.item_no: item for item in await item_repo.list_by_inquiry(inquiry_id)
        }
        for item_no in item_nos:
            db_item = existing_db_items.get(item_no)
            if db_item is None:
                db_item = await item_repo.add(
                    InquiryItem(inquiry_id=inquiry_id, item_no=item_no)
                )
                await session.flush()
                existing_db_items[item_no] = db_item
            for (field_id, fn), field_state in agent_state.fields.items():
                if fn == item_no:
                    await _persist_field(
                        session,
                        field_def_id_by_field_id,
                        field_state,
                        inquiry_item_id=db_item.id,
                        existing_case_or_item=existing_items.get(str(item_no), {}),
                    )

        note_repo = InquiryNoteRepository(session)
        for note in agent_state.case_notes:
            note_repo_obj = InquiryNote(
                inquiry_id=inquiry_id,
                scope="case",
                content=note["content"],
                source_type=note.get("source_type"),
                source_file=note.get("source_file"),
                source_location=note.get("source_location"),
            )
            await note_repo.add(note_repo_obj)
        for item_no, notes in agent_state.item_notes.items():
            db_item = existing_db_items.get(item_no)
            if db_item is None:
                continue
            for note in notes:
                await note_repo.add(
                    InquiryNote(
                        inquiry_id=inquiry_id,
                        inquiry_item_id=db_item.id,
                        scope="item",
                        content=note["content"],
                        source_type=note.get("source_type"),
                        source_file=note.get("source_file"),
                        source_location=note.get("source_location"),
                    )
                )

        agent_run = await AgentRunRepository(session).get(agent_run_id)
        if agent_run is not None:
            agent_run.status = "succeeded"
            agent_run.stage = "completed"
            agent_run.progress_percent = 100
            agent_run.finished_at = datetime.now(UTC)

        await session.commit()

    state.clear_state(inquiry_id)
    return _ok(
        {
            "inquiry_id": inquiry_id,
            "saved": True,
            "field_count": len(agent_state.fields),
        }
    )


async def persist_partial_structured_result(inquiry_id: int) -> int:
    """強制停止時に、AGENT-02が既に受け付けた項目だけを未完了状態で保存する。"""
    agent_state = state.get_state(inquiry_id)
    if not agent_state.fields:
        return 0

    async with AsyncSessionLocal() as session:
        inquiry = await InquiryRepository(session).get(inquiry_id)
        if inquiry is None:
            return 0
        field_def_id_by_field_id = {
            f.field_id: f.id for f in await FieldDefinitionRepository(session).list()
        }
        existing = agent_state.existing or {}
        existing_case = existing.get("case_fields", {})
        existing_items = existing.get("items", {})
        item_repo = InquiryItemRepository(session)
        existing_db_items = {
            item.item_no: item for item in await item_repo.list_by_inquiry(inquiry_id)
        }

        saved = 0
        for (field_id, item_no), field_state in agent_state.fields.items():
            # classify_status未実行の値を自動採用しない。候補・Evidenceは保持する。
            if field_state.status is None:
                field_state.value = None
                field_state.status = "review"
                field_state.reason_type = "parse_error"
            if item_no is None:
                await _persist_field(
                    session,
                    field_def_id_by_field_id,
                    field_state,
                    inquiry_id=inquiry_id,
                    existing_case_or_item=existing_case,
                )
            else:
                db_item = existing_db_items.get(item_no)
                if db_item is None:
                    db_item = await item_repo.add(
                        InquiryItem(inquiry_id=inquiry_id, item_no=item_no)
                    )
                    await session.flush()
                    existing_db_items[item_no] = db_item
                await _persist_field(
                    session,
                    field_def_id_by_field_id,
                    field_state,
                    inquiry_item_id=db_item.id,
                    existing_case_or_item=existing_items.get(str(item_no), {}),
                )
            saved += 1

        await session.commit()
    state.clear_state(inquiry_id)
    return saved


AGENT02_TOOLS = [
    load_existing_inquiry,
    compare_and_merge_candidates,
    evaluate_explicit_correction,
    classify_status,
    web_search_company_info,
    save_structured_result,
]

agent02_server = create_sdk_mcp_server(
    name="agent02", version="1.0.0", tools=AGENT02_TOOLS
)

AGENT02_MCP_TOOL_NAMES = [f"mcp__agent02__{t.name}" for t in AGENT02_TOOLS]
# AGENT-02は唯一、組み込みWebSearchツールを併用する（web_search_company_infoが登録専用の
# ラッパーであり、実際の検索自体はWebSearchで行う。guardrails.guard_web_searchで内容制限）
AGENT02_ALLOWED_TOOL_NAMES = [*AGENT02_MCP_TOOL_NAMES, "WebSearch"]
