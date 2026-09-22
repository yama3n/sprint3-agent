import pytest

from app.agent.agent01.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS
from app.agent.agent01.validation import (
    build_case_fields,
    build_extraction_result,
    build_item_fields,
    validate_extraction_result,
)


def _candidate(field_id: str, value: str | None, **overrides) -> dict:
    base = {
        "field_id": field_id,
        "value": value,
        "source_type": "pdf",
        "source_file": "a.pdf",
        "source_location": "p.1",
        "quoted_text": value,
    }
    base.update(overrides)
    return base


def test_build_case_fields_groups_candidates_and_fills_all_keys() -> None:
    candidates = [
        _candidate("requester", "東西石油開発"),
        _candidate("requester", "東西石油開発株式会社"),
        _candidate("project_name", "北海油田 鋼管更新案件"),
    ]

    result = build_case_fields(candidates)

    assert set(result.keys()) == set(CASE_FIELD_IDS)
    assert len(result["requester"]) == 2
    assert len(result["project_name"]) == 1
    assert result["inquiry_date"] == []  # 記載なし項目は空配列


def test_build_case_fields_rejects_unknown_field_id() -> None:
    with pytest.raises(ValueError, match="未知のfield_id"):
        build_case_fields([_candidate("not_a_real_field", "x")])


def test_build_case_fields_rejects_missing_required_key() -> None:
    bad = _candidate("requester", "x")
    del bad["source_file"]
    with pytest.raises(ValueError, match="必須キー"):
        build_case_fields([bad])


def test_build_item_fields_groups_by_item_no_and_fills_all_keys() -> None:
    items = [
        {"item_no": 1, "candidates": [_candidate("grade", "L80", source_type="excel")]},
        {"item_no": 2, "candidates": []},
    ]

    result = build_item_fields(items)

    assert set(result.keys()) == {1, 2}
    assert set(result[1].keys()) == set(ITEM_FIELD_IDS)
    assert len(result[1]["grade"]) == 1
    assert result[2]["grade"] == []


def test_build_item_fields_rejects_unknown_field_id() -> None:
    with pytest.raises(ValueError, match="未知のfield_id"):
        build_item_fields(
            [{"item_no": 1, "candidates": [_candidate("requester", "x")]}]
        )


def test_null_value_is_not_retained_as_a_candidate() -> None:
    case_fields = build_case_fields([_candidate("requester", None)])
    item_fields = build_item_fields(
        [
            {
                "item_no": 1,
                "candidates": [_candidate("thread_type", None, source_type="excel")],
            }
        ]
    )

    assert case_fields["requester"] == []
    assert item_fields[1]["thread_type"] == []


def test_validate_extraction_result_passes_for_complete_result() -> None:
    case_fields = build_case_fields([_candidate("requester", "東西石油開発")])
    item_fields = build_item_fields([{"item_no": 1, "candidates": []}])
    result = build_extraction_result(
        inquiry_id="INQ-1",
        source_files=["a.pdf"],
        case_fields=case_fields,
        item_fields=item_fields,
        case_notes=[],
        item_notes={},
    )

    errors = validate_extraction_result(result, expected_source_files=["a.pdf"])

    assert errors == []


def test_validate_extraction_result_flags_missing_source_file() -> None:
    case_fields = build_case_fields([])
    result = build_extraction_result(
        inquiry_id="INQ-1",
        source_files=["a.pdf"],
        case_fields=case_fields,
        item_fields={},
        case_notes=[],
        item_notes={},
    )

    errors = validate_extraction_result(
        result, expected_source_files=["a.pdf", "b.xlsx"]
    )

    assert any("source_files" in e for e in errors)


def test_validate_extraction_result_flags_missing_case_field_key() -> None:
    result = build_extraction_result(
        inquiry_id="INQ-1",
        source_files=["a.pdf"],
        case_fields={"requester": []},  # 他の13項目キーが欠落
        item_fields={},
        case_notes=[],
        item_notes={},
    )

    errors = validate_extraction_result(result, expected_source_files=["a.pdf"])

    assert any("case_fields" in e for e in errors)


def test_build_case_fields_merges_into_existing() -> None:
    """分割呼び出し: 2回目の呼び出しで1回目の候補が失われない。"""
    first = build_case_fields([_candidate("requester", "東西石油開発")])

    second = build_case_fields([_candidate("project_name", "北海油田")], existing=first)

    assert len(second["requester"]) == 1
    assert len(second["project_name"]) == 1
    assert set(second.keys()) == set(CASE_FIELD_IDS)
    # existing 側は破壊しない（コピーして積む）
    assert first["project_name"] == []


def test_build_item_fields_merges_new_and_existing_items() -> None:
    """分割呼び出し: 既存品目への追記と、新しい品目の追加が同時にできる。"""
    first = build_item_fields(
        [
            {
                "item_no": 1,
                "candidates": [_candidate("grade", "L80", source_type="excel")],
            }
        ]
    )

    second = build_item_fields(
        [
            {
                "item_no": 1,
                "candidates": [_candidate("quantity", "240", source_type="excel")],
            },
            {
                "item_no": 2,
                "candidates": [_candidate("grade", "J55", source_type="excel")],
            },
        ],
        existing=first,
    )

    assert set(second.keys()) == {1, 2}
    assert len(second[1]["grade"]) == 1
    assert len(second[1]["quantity"]) == 1
    assert len(second[2]["grade"]) == 1
    assert set(second[2].keys()) == set(ITEM_FIELD_IDS)
    assert first[1]["quantity"] == []
