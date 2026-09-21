"""AGENT-01の候補値グルーピング・ExtractionResult組み立て（決定論的処理）。

candidateの「値」自体はAGENT-01の実行ループ（Claude自身）が文書を読んで判断する
（agent-development.md追加要件: ルールベース処理でAGENT-01の意味判断を代替しない）。
このモジュールは受け取った候補を固定項目スキーマに沿って検証・整形するだけの、
入出力の決まった決定的関数群（TDD対象）。
"""

from app.agent.agent01.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS, SOURCE_TYPES

REQUIRED_CANDIDATE_KEYS = (
    "field_id",
    "value",
    "source_type",
    "source_file",
    "source_location",
    "quoted_text",
)


def _validate_candidate(candidate: dict, valid_field_ids: list[str]) -> None:
    missing = [k for k in REQUIRED_CANDIDATE_KEYS if k not in candidate]
    if missing:
        raise ValueError(f"候補に必須キーが不足しています: {missing}")
    if candidate["field_id"] not in valid_field_ids:
        raise ValueError(f"未知のfield_id: {candidate['field_id']}")
    if candidate["source_type"] not in SOURCE_TYPES:
        raise ValueError(f"不正なsource_type: {candidate['source_type']}")


def build_case_fields(candidates: list[dict]) -> dict[str, list[dict]]:
    """A項目（案件全体、14固定項目）の候補値配列を組み立てる。
    記載が見つからなかった項目もキー自体は必須のため、全14項目を空配列で初期化する。"""
    result: dict[str, list[dict]] = {field_id: [] for field_id in CASE_FIELD_IDS}
    for candidate in candidates:
        _validate_candidate(candidate, CASE_FIELD_IDS)
        result[candidate["field_id"]].append(candidate)
    return result


def build_item_fields(items: list[dict]) -> dict[int, dict[str, list[dict]]]:
    """B項目（品目ごと、8固定項目）の候補値配列を組み立てる。
    items: [{"item_no": int, "candidates": [ExtractionCandidate, ...]}]"""
    result: dict[int, dict[str, list[dict]]] = {}
    for item in items:
        item_no = item["item_no"]
        bucket = result.setdefault(
            item_no, {field_id: [] for field_id in ITEM_FIELD_IDS}
        )
        for candidate in item.get("candidates", []):
            _validate_candidate(candidate, ITEM_FIELD_IDS)
            bucket[candidate["field_id"]].append(candidate)
    return result


def build_extraction_result(
    inquiry_id: str,
    source_files: list[str],
    case_fields: dict[str, list[dict]],
    item_fields: dict[int, dict[str, list[dict]]],
    case_notes: list[dict],
    item_notes: dict[int, list[dict]],
) -> dict:
    """agent-plan.md「2. エージェント間データフロー」の ExtractionResult 形状。"""
    return {
        "inquiry_id": inquiry_id,
        "source_files": source_files,
        "case_fields": case_fields,
        "item_fields": item_fields,
        "case_notes": case_notes,
        "item_notes": item_notes,
    }


def validate_extraction_result(
    result: dict, expected_source_files: list[str]
) -> list[str]:
    """agent-plan.md AGENT-01完了条件(a)(b)(c)の自動チェック。空リストなら合格。

    (c)（候補の必須キー）は build_case_fields/build_item_fields が候補追加時点で
    _validate_candidate により既に保証しているため、ここでは(a)(b)のみ再検証する。
    """
    errors: list[str] = []

    missing_files = set(expected_source_files) - set(result.get("source_files", []))
    if missing_files:
        errors.append(
            f"source_filesに含まれていないファイルがあります: {sorted(missing_files)}"
        )

    case_fields = result.get("case_fields", {})
    missing_case = set(CASE_FIELD_IDS) - set(case_fields.keys())
    if missing_case:
        errors.append(
            f"case_fieldsに存在しないfield_idがあります: {sorted(missing_case)}"
        )

    for item_no, fields in result.get("item_fields", {}).items():
        missing_item = set(ITEM_FIELD_IDS) - set(fields.keys())
        if missing_item:
            errors.append(
                f"item_fields[{item_no}]に存在しないfield_idがあります: {sorted(missing_item)}"
            )

    return errors
