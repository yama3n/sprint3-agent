import pytest

from app.agent.agent02.guardrails import guard_web_search


@pytest.mark.asyncio
async def test_guard_allows_non_web_search_tools() -> None:
    result = await guard_web_search(
        {"tool_name": "mcp__agent02__classify_status", "tool_input": {}}, None, None
    )
    assert result == {}


@pytest.mark.asyncio
async def test_guard_allows_company_info_query() -> None:
    result = await guard_web_search(
        {
            "tool_name": "WebSearch",
            "tool_input": {"query": "東西石油開発株式会社 公式サイト"},
        },
        None,
        None,
    )
    assert result == {}


@pytest.mark.asyncio
async def test_guard_denies_query_with_customer_specific_term() -> None:
    result = await guard_web_search(
        {"tool_name": "WebSearch", "tool_input": {"query": "鋼管 数量 320本"}},
        None,
        None,
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.asyncio
async def test_guard_denies_delivery_date_query() -> None:
    result = await guard_web_search(
        {"tool_name": "WebSearch", "tool_input": {"query": "希望納期 2027年"}},
        None,
        None,
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
