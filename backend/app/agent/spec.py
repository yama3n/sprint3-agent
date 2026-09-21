"""複数エージェント（AGENT-01/AGENT-02）を runner.py/jobs.py が共通に扱うための型。

agent-plan.md の各エージェントの Part1「完了条件・停止条件」・Part2「ツール一覧」・
「ガードレール」を1つのAgentSpecへ集約する。runner/jobsはこの値のみを見て動作し、
エージェント固有の知識を持たない。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSpec:
    name: str
    system_prompt: str
    max_turns: int
    inner_timeout_s: int
    inactivity_timeout_s: int
    outer_timeout_s: int
    mcp_server: Any
    # ClaudeAgentOptions.mcp_servers に渡す辞書キー。ツール名の実際のプレフィックス
    # （mcp__{mcp_label}__{tool_name}）はこのキーで決まる — create_sdk_mcp_server(name=...)
    # の値ではない。allowed_tool_names はこのラベルと必ず一致させること（不一致は権限拒否の原因）
    mcp_label: str
    allowed_tool_names: list[str]
    # PreToolUse等のガードレール（agent-development.md: お願いに頼らずhooksで強制する）
    hooks: dict[str, Any] | None = field(default=None)

    def __post_init__(self) -> None:
        assert (
            self.inactivity_timeout_s < self.inner_timeout_s < self.outer_timeout_s
        ), f"[{self.name}] タイムアウトは 無応答 < 内側 < 外側 の順でなければならない。"
