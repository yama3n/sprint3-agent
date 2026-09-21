"""AGENT-02実行中の統合状態（プロセス内・inquiry_idごと）。

compare_and_merge_candidates → evaluate_explicit_correction → classify_status →
web_search_company_info の各ツール呼び出しが同じ per-field レコードを段階的に更新し、
save_structured_result が最終的にDBへ永続化する。jobs.py/agent01と同じ「教材の割り切り」。
"""

from dataclasses import dataclass, field


@dataclass
class FieldState:
    field_id: str
    item_no: int | None = None
    value: str | None = None
    status: str | None = None  # "ok" | "review"（classify_status確定まではNone）
    reason_type: str | None = None
    is_web_supplemented: bool = False
    candidates: list[dict] = field(default_factory=list)


@dataclass
class Agent02State:
    # key: (field_id, item_no)  item_noはcase項目ならNone
    fields: dict[tuple[str, int | None], FieldState] = field(default_factory=dict)
    case_notes: list[dict] = field(default_factory=list)
    item_notes: dict[int, list[dict]] = field(default_factory=dict)
    existing: dict | None = (
        None  # load_existing_inquiryの結果（追加アップロード時のみ）
    )


_states: dict[int, Agent02State] = {}


def get_state(inquiry_id: int) -> Agent02State:
    return _states.setdefault(inquiry_id, Agent02State())


def clear_state(inquiry_id: int) -> None:
    _states.pop(inquiry_id, None)
