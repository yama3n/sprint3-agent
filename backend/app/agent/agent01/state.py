"""AGENT-01実行中の抽出状態（プロセス内・inquiry_idごと）。

1引合につき1回のAGENT-01実行が完了するまでの一時的な集約領域。extract_case_fields/
extract_item_fields/extract_supplementary_notesの呼び出し結果をここに積み上げ、
emit_extraction_resultが最終的なExtractionResultとしてDB（extraction_results）へ永続化する。
jobs.py の `_jobs` と同じ「教材の割り切り」（プロセス内保持、再起動で消える）。
"""

from dataclasses import dataclass, field


@dataclass
class ExtractionState:
    case_fields: dict[str, list[dict]] | None = None
    item_fields: dict[int, dict[str, list[dict]]] | None = None
    case_notes: list[dict] = field(default_factory=list)
    item_notes: dict[int, list[dict]] = field(default_factory=dict)
    parse_errors: list[dict] = field(default_factory=list)


_states: dict[int, ExtractionState] = {}


def get_state(inquiry_id: int) -> ExtractionState:
    return _states.setdefault(inquiry_id, ExtractionState())


def clear_state(inquiry_id: int) -> None:
    _states.pop(inquiry_id, None)
