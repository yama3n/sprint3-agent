"""AGENT-02のスキーマ定義。固定項目IDはAGENT-01と共有する（field_definitionsが唯一の正）。"""

from app.agent.agent01.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS  # noqa: F401 (re-export)

REASON_TYPES = (
    "missing",
    "conflict",
    "ambiguous",
    "multiple_candidates",
    "parse_error",
)
STATUSES = ("ok", "review")

# FUNC-04: 顧客固有の数量・希望納期・案件固有の要求仕様等はWeb補完の対象外。
# 公開情報で客観的に確認可能な「企業情報」系の項目のみをWeb補完の対象として許可する
# （agent-plan.md 3章ガードレール「してはいけない操作」に対応する構造的制約）。
WEB_SUPPLEMENT_ALLOWED_CASE_FIELD_IDS = frozenset(
    {"requester", "engineering_company", "epc", "end_user"}
)

# Web検索クエリに含めてはならない語（顧客固有情報の漏洩防止。FUNC-04）
FORBIDDEN_WEB_SEARCH_TERMS = (
    "数量",
    "本数",
    "個数",
    "納期",
    "希望納期",
    "見積",
    "価格",
    "単価",
)
