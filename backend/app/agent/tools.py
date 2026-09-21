"""カスタムツール群: docs/requirements/agent-plan.md「ツール一覧」と1対1で対応させる。

- ツールは入出力の決まった関数として実装し、単体テスト（TDD）の対象にする
- 副作用（write）を持つツールは agent-plan.md のガードレールと突き合わせる
- ツール名は mcp__app__{tool_name} 形式で allowed_tools に列挙する

Foundation段階（Slice 0-7）では疎通確認用の ping のみ。build-loopのエージェントスライスが
agent-plan.md の AGENT-01（parse_excel/parse_pdf/parse_eml/extract_case_fields/...）・
AGENT-02（load_existing_inquiry/compare_and_merge_candidates/...）のツールをここに追加する。
"""

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


@tool("ping", "疎通確認用。メッセージをそのまま返す", {"message": str})
async def ping(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"pong: {args['message']}"}]}


# build-loop（エージェントスライス）がここに agent-plan.md のツールを追加していく
AGENT_TOOLS = [ping]

agent_server = create_sdk_mcp_server(name="app", version="1.0.0", tools=AGENT_TOOLS)

# allowed_tools に渡す名前（mcp__{server}__{tool}）
ALLOWED_TOOL_NAMES = ["mcp__app__ping"]
