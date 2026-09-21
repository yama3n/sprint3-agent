"""AGENT-02のガードレール（PreToolUse hook）。

agent-development.md「してはいけない操作はhooks/disallowed_toolsで強制する」に対応する。
AGENT-02は唯一Web検索（組み込みWebSearchツール）を持つエージェントであり、FUNC-04
「顧客固有の数量・希望納期・案件固有の要求仕様等はWeb補完の対象外」を、プロンプトのお願い
だけでなくクエリ内容の機械チェックで強制する。
"""

from typing import Any

from app.agent.agent02.schema import FORBIDDEN_WEB_SEARCH_TERMS


def _contains_forbidden_term(query: str) -> str | None:
    for term in FORBIDDEN_WEB_SEARCH_TERMS:
        if term in query:
            return term
    return None


async def guard_web_search(
    input_data: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    """WebSearchツール呼び出し前に、クエリに顧客固有情報の語が含まれていないか検査する。"""
    if input_data.get("tool_name") != "WebSearch":
        return {}

    query = str(input_data.get("tool_input", {}).get("query", ""))
    forbidden = _contains_forbidden_term(query)
    if forbidden:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"検索クエリに顧客固有情報とみられる語「{forbidden}」が含まれています。"
                    "Web補完の対象は公開情報で客観的に確認可能な企業情報等に限定されます"
                    "（FUNC-04）。顧客固有の数量・納期・仕様等は検索せず要確認のまま保持してください。"
                ),
            }
        }
    return {}
