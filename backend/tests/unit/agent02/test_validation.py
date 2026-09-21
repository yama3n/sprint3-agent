import pytest

from app.agent.agent02.state import Agent02State, FieldState
from app.agent.agent02.validation import (
    validate_candidate,
    validate_completion,
    validate_field_decision,
    validate_field_ref,
)


def test_validate_field_ref_accepts_valid_case_field() -> None:
    validate_field_ref("requester", None)


def test_validate_field_ref_rejects_unknown_case_field() -> None:
    with pytest.raises(ValueError, match="未知のfield_id"):
        validate_field_ref("not_a_field", None)


def test_validate_field_ref_rejects_case_field_id_used_as_item_field() -> None:
    with pytest.raises(ValueError, match="未知のfield_id"):
        validate_field_ref("requester", 1)


def test_validate_candidate_requires_web_metadata_for_web_source() -> None:
    with pytest.raises(ValueError, match="Web出典"):
        validate_candidate({"value": "x", "source_type": "web"})
    validate_candidate(
        {
            "value": "x",
            "source_type": "web",
            "web_url": "https://example.com",
            "web_source_name": "Example",
        }
    )


def test_validate_field_decision_ok_requires_candidate() -> None:
    state = FieldState(field_id="requester", status="ok", candidates=[])
    errors = validate_field_decision(state)
    assert any("出典" in e for e in errors)


def test_validate_field_decision_review_missing_allows_zero_candidates() -> None:
    state = FieldState(
        field_id="requester", status="review", reason_type="missing", candidates=[]
    )
    assert validate_field_decision(state) == []


def test_validate_field_decision_review_conflict_requires_candidates() -> None:
    state = FieldState(
        field_id="requester", status="review", reason_type="conflict", candidates=[]
    )
    errors = validate_field_decision(state)
    assert any("候補が1件も" in e for e in errors)


def test_validate_field_decision_web_supplemented_requires_web_candidate() -> None:
    state = FieldState(
        field_id="requester",
        status="ok",
        is_web_supplemented=True,
        candidates=[{"value": "x", "source_type": "excel"}],
    )
    errors = validate_field_decision(state)
    assert any("Web出典" in e for e in errors)


def test_validate_completion_flags_missing_field_judgement() -> None:
    agent_state = Agent02State()
    errors = validate_completion(agent_state, item_nos=[1])
    assert any("requester" in e for e in errors)
    assert any("item=1" in e for e in errors)


def test_validate_completion_passes_when_all_fields_judged() -> None:
    from app.agent.agent02.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS

    agent_state = Agent02State()
    for field_id in CASE_FIELD_IDS:
        agent_state.fields[(field_id, None)] = FieldState(
            field_id=field_id, status="review", reason_type="missing", candidates=[]
        )
    for field_id in ITEM_FIELD_IDS:
        agent_state.fields[(field_id, 1)] = FieldState(
            field_id=field_id,
            item_no=1,
            status="review",
            reason_type="missing",
            candidates=[],
        )

    assert validate_completion(agent_state, item_nos=[1]) == []
