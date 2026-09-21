"""AGENT-01のツール群（Claude Agent SDK @tool）。agent-plan.md §3 Part2のツール一覧と1対1。

- parse_excel/parse_pdf/parse_eml: 決定論的なファイル解析（parsing.py）。
- extract_case_fields/extract_item_fields/extract_supplementary_notes: AGENT-01自身
  （呼び出し元のClaude）が文書を読んで意味理解に基づき判断した候補値を受け取り、固定項目
  スキーマに沿って検証・集約する（validation.py）。ここで値そのものを生成することはない
  （agent-development.md追加要件: ルールベース処理でAGENT-01の意味判断を代替しない）。
- emit_extraction_result: 集約結果をExtractionResultとして完了条件を自動チェックし、
  extraction_results へ保存する（write。inquiries本体・確認中/確定済みJSONへの書き込み権限は
  持たない＝AGENT-02の責務との分離、agent-plan.md 3章ガードレール）。
"""

import json
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.agent.agent01 import state, validation
from app.agent.agent01.parsing import parse_eml_file, parse_excel_file, parse_pdf_file
from app.agent.agent01.tool_schemas import (
    EMIT_EXTRACTION_RESULT_SCHEMA,
    EXTRACT_CASE_FIELDS_SCHEMA,
    EXTRACT_ITEM_FIELDS_SCHEMA,
    EXTRACT_SUPPLEMENTARY_NOTES_SCHEMA,
    PARSE_FILE_SCHEMA,
)
from app.core.db import AsyncSessionLocal
from app.models.agent_run import ExtractionResult, ParsedDocument
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.extraction_result_repository import ExtractionResultRepository
from app.repositories.inquiry_file_repository import InquiryFileRepository
from app.repositories.parsed_document_repository import ParsedDocumentRepository


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
    "parse_excel",
    "Excelファイルの表構造（シート・セル）をテキスト化する",
    PARSE_FILE_SCHEMA,
)
async def parse_excel(args: dict[str, Any]) -> dict[str, Any]:
    file_id = args["file_id"]
    async with AsyncSessionLocal() as session:
        inquiry_file = await InquiryFileRepository(session).get(file_id)
        if inquiry_file is None:
            return _error("FILE_NOT_FOUND")
        file_name = inquiry_file.file_name
        try:
            content = parse_excel_file(inquiry_file.storage_path)
        except (
            Exception
        ) as e:  # 対応形式でも壊れたファイルはparse_error候補としてAGENT-01自身が扱う
            return _error(f"PARSE_ERROR: {e!r}")
        await ParsedDocumentRepository(session).add(
            ParsedDocument(file_id=inquiry_file.id, content=content)
        )
        await session.commit()
    return _ok({"file_id": file_id, "file_name": file_name, "sheets": content})


@tool("parse_pdf", "PDFの本文をページ単位でテキスト化する", PARSE_FILE_SCHEMA)
async def parse_pdf(args: dict[str, Any]) -> dict[str, Any]:
    file_id = args["file_id"]
    async with AsyncSessionLocal() as session:
        inquiry_file = await InquiryFileRepository(session).get(file_id)
        if inquiry_file is None:
            return _error("FILE_NOT_FOUND")
        file_name = inquiry_file.file_name
        try:
            content = parse_pdf_file(inquiry_file.storage_path)
        except Exception as e:
            return _error(f"PARSE_ERROR: {e!r}")
        await ParsedDocumentRepository(session).add(
            ParsedDocument(file_id=inquiry_file.id, content=content)
        )
        await session.commit()
    return _ok({"file_id": file_id, "file_name": file_name, "pages": content})


@tool(
    "parse_eml", "メールの件名・本文をセクション単位でテキスト化する", PARSE_FILE_SCHEMA
)
async def parse_eml(args: dict[str, Any]) -> dict[str, Any]:
    file_id = args["file_id"]
    async with AsyncSessionLocal() as session:
        inquiry_file = await InquiryFileRepository(session).get(file_id)
        if inquiry_file is None:
            return _error("FILE_NOT_FOUND")
        file_name = inquiry_file.file_name
        try:
            content = parse_eml_file(inquiry_file.storage_path)
        except Exception as e:
            return _error(f"PARSE_ERROR: {e!r}")
        await ParsedDocumentRepository(session).add(
            ParsedDocument(file_id=inquiry_file.id, content=content)
        )
        await session.commit()
    return _ok({"file_id": file_id, "file_name": file_name, "sections": content})


@tool(
    "extract_case_fields",
    "パース済みテキストから読み取ったA項目（引合・案件全体、14固定項目）の候補値と出典を登録する。"
    "値の判断はこのツールを呼ぶあなた自身が行うこと（このツールは検証・集約のみ行う）。",
    EXTRACT_CASE_FIELDS_SCHEMA,
)
async def extract_case_fields(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    extraction_state = state.get_state(inquiry_id)
    try:
        # 複数回に分けて呼ばれた場合は追記する（巨大な単一ペイロードを避けられるように）
        case_fields = validation.build_case_fields(
            args["candidates"], existing=extraction_state.case_fields
        )
    except ValueError as e:
        return _error(str(e))
    extraction_state.case_fields = case_fields
    filled = [k for k, v in case_fields.items() if v]
    return _ok({"registered_field_ids": filled, "total_field_keys": len(case_fields)})


@tool(
    "extract_item_fields",
    "パース済みテキストから読み取ったB項目（品目ごと、8固定項目）の候補値と出典を品目単位で登録する。"
    "値の判断はこのツールを呼ぶあなた自身が行うこと（このツールは検証・集約のみ行う）。"
    "品目数が多い場合は数品目ずつ複数回に分けて呼んでよい（呼び出しごとに追記される）。",
    EXTRACT_ITEM_FIELDS_SCHEMA,
)
async def extract_item_fields(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    extraction_state = state.get_state(inquiry_id)
    try:
        # 品目が多い場合に分割して呼べるよう、品目単位で追記する
        item_fields = validation.build_item_fields(
            args["items"], existing=extraction_state.item_fields
        )
    except ValueError as e:
        return _error(str(e))
    extraction_state.item_fields = item_fields
    return _ok({"registered_items": list(item_fields.keys())})


@tool(
    "extract_supplementary_notes",
    "固定項目に当てはまらない情報を、案件全体／品目固有を区別した配列として登録する。",
    EXTRACT_SUPPLEMENTARY_NOTES_SCHEMA,
)
async def extract_supplementary_notes(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    extraction_state = state.get_state(inquiry_id)
    extraction_state.case_notes = args.get("case_notes", [])
    extraction_state.item_notes = {
        entry["item_no"]: entry["notes"] for entry in args.get("item_notes", [])
    }
    return _ok(
        {
            "case_note_count": len(extraction_state.case_notes),
            "item_note_count": sum(
                len(v) for v in extraction_state.item_notes.values()
            ),
        }
    )


@tool(
    "emit_extraction_result",
    "抽出結果をExtractionResultスキーマにまとめ、完了条件を自動チェックしたうえでAGENT-02が"
    "参照できる形で保存する。extract_case_fields/extract_item_fieldsを先に呼んでおくこと。",
    EMIT_EXTRACTION_RESULT_SCHEMA,
)
async def emit_extraction_result(args: dict[str, Any]) -> dict[str, Any]:
    inquiry_id = args["inquiry_id"]
    agent_run_id = args["agent_run_id"]
    source_files = args["source_files"]

    extraction_state = state.get_state(inquiry_id)
    if extraction_state.case_fields is None:
        return _error(
            "extract_case_fieldsが未実行です。先にA項目の抽出を行ってください。"
        )
    if extraction_state.item_fields is None:
        return _error(
            "extract_item_fieldsが未実行です。先にB項目の抽出を行ってください。"
        )

    result = validation.build_extraction_result(
        inquiry_id=inquiry_id,
        source_files=source_files,
        case_fields=extraction_state.case_fields,
        item_fields=extraction_state.item_fields,
        case_notes=extraction_state.case_notes,
        item_notes=extraction_state.item_notes,
    )
    errors = validation.validate_extraction_result(
        result, expected_source_files=source_files
    )
    if errors:
        return _error(
            "ExtractionResultの完了条件を満たしていません: " + " / ".join(errors)
        )

    # JSON永続化境界: item_fields/item_notesのitem_noキーは文字列化する（Postgres JSON列は
    # int キーを保持できず、読み出し時にAGENT-02が誤解しないよう明示的に変換する）
    payload = {
        **result,
        "item_fields": {str(k): v for k, v in result["item_fields"].items()},
        "item_notes": {str(k): v for k, v in result["item_notes"].items()},
    }

    async with AsyncSessionLocal() as session:
        await ExtractionResultRepository(session).add(
            ExtractionResult(
                inquiry_id=inquiry_id, agent_run_id=agent_run_id, payload=payload
            )
        )
        agent_run_repo = AgentRunRepository(session)
        agent_run = await agent_run_repo.get(agent_run_id)
        if agent_run is not None:
            # ここで completed にすると、オーケストレータがAGENT-02行を作るまでの間、
            # status APIが全パイプライン完了と誤認する。引き渡し中は非終端状態を維持し、
            # AGENT-01完了とAGENT-02開始をオーケストレータが同一commitで切り替える。
            agent_run.status = "running"
            agent_run.stage = "structuring"
            agent_run.progress_percent = 55
        await session.commit()

    state.clear_state(inquiry_id)
    return _ok(
        {
            "inquiry_id": inquiry_id,
            "saved": True,
            "case_field_candidate_count": sum(
                len(v) for v in result["case_fields"].values()
            ),
            "item_count": len(result["item_fields"]),
        }
    )


AGENT01_TOOLS = [
    parse_excel,
    parse_pdf,
    parse_eml,
    extract_case_fields,
    extract_item_fields,
    extract_supplementary_notes,
    emit_extraction_result,
]

agent01_server = create_sdk_mcp_server(
    name="agent01", version="1.0.0", tools=AGENT01_TOOLS
)

AGENT01_ALLOWED_TOOL_NAMES = [f"mcp__agent01__{t.name}" for t in AGENT01_TOOLS]
