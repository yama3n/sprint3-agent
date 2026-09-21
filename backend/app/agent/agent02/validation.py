"""AGENT-02の統合結果の検証（決定論的処理）。

「どの値を採用するか」「矛盾をどう扱うか」等の判断はAGENT-02自身（Claude）が行う
（agent-development.md追加要件: 単純なif/elseでAGENT-02の意味判断を代替しない）。
このモジュールは受け取った判断結果が完了条件を満たす構造になっているかを検証するだけ。
"""

from app.agent.agent01.schema import SOURCE_TYPES
from app.agent.agent02.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS, REASON_TYPES
from app.agent.agent02.state import Agent02State, FieldState


def validate_field_ref(field_id: str, item_no: int | None) -> None:
    valid_ids = ITEM_FIELD_IDS if item_no is not None else CASE_FIELD_IDS
    if field_id not in valid_ids:
        scope = "item" if item_no is not None else "case"
        raise ValueError(f"未知のfield_id（{scope}スコープ）: {field_id}")


def validate_candidate(candidate: dict) -> None:
    required = ("value", "source_type")
    missing = [k for k in required if k not in candidate]
    if missing:
        raise ValueError(f"候補に必須キーが不足しています: {missing}")
    if candidate["source_type"] not in SOURCE_TYPES:
        raise ValueError(f"不正なsource_type: {candidate['source_type']}")
    if candidate["source_type"] == "web":
        web_missing = [
            k for k in ("web_url", "web_source_name") if not candidate.get(k)
        ]
        if web_missing:
            raise ValueError(f"Web出典に必須キーが不足しています: {web_missing}")


def validate_field_decision(state: FieldState) -> list[str]:
    """1項目分のstatus/reason_type/candidatesの整合性チェック（agent-plan.md完了条件(b)(c)(d)）。"""
    errors: list[str] = []
    label = f"{state.field_id}" + (f"[item={state.item_no}]" if state.item_no else "")

    if state.status not in ("ok", "review"):
        errors.append(f"{label}: statusが未設定または不正です")
        return errors

    if state.status == "ok":
        if not state.candidates:
            errors.append(f"{label}: status=okだが出典（候補）が1件もありません")
    else:  # review
        if state.reason_type not in REASON_TYPES:
            errors.append(f"{label}: status=reviewだがreason_typeが不正です")
        elif state.reason_type != "missing" and not state.candidates:
            errors.append(
                f"{label}: reason_type={state.reason_type}だが候補が1件もありません"
            )

    if state.is_web_supplemented:
        has_web_source = any(
            c.get("source_type") == "web"
            and c.get("web_url")
            and c.get("web_source_name")
            for c in state.candidates
        )
        if not has_web_source:
            errors.append(
                f"{label}: is_web_supplemented=trueだがWeb出典（URL/参照元）がありません"
            )

    return errors


def validate_completion(agent_state: Agent02State, item_nos: list[int]) -> list[str]:
    """agent-plan.md AGENT-02完了条件(a)(b)(c)(d)の自動チェック。空リストなら合格。"""
    errors: list[str] = []

    for field_id in CASE_FIELD_IDS:
        key = (field_id, None)
        if key not in agent_state.fields:
            errors.append(
                f"case field '{field_id}' の判定(classify_status)が未実行です"
            )
        else:
            errors.extend(validate_field_decision(agent_state.fields[key]))

    for item_no in item_nos:
        for field_id in ITEM_FIELD_IDS:
            key = (field_id, item_no)
            if key not in agent_state.fields:
                errors.append(
                    f"item field '{field_id}'[item={item_no}] の判定が未実行です"
                )
            else:
                errors.extend(validate_field_decision(agent_state.fields[key]))

    return errors
