"""エージェント実行ループ。

タイムアウトの責務分担:
- 内側（このファイル）: spec.inner_timeout_s（実行全体）と spec.inactivity_timeout_s（無応答=
  ハング検知）。発火したらトレースに stop_reason を記録して整然と終了する。
  agent-plan.md の「強制停止」に対応。
- 外側（jobs.py）: spec.outer_timeout_s。内側が機能しなかった場合（SDK サブプロセスの
  ハング・キャンセル不能など）の最後の砦。発火 = 内側の異常であり、バグとして扱う。

直接呼ばない: 起動は必ず jobs.start_agent_job() 経由（バックグラウンド実行 + 外側タイムアウト）。

AGENT-01/AGENT-02はそれぞれ固有の AgentSpec（system_prompt/timeouts/tools/hooks）を持つ。
このファイルはどちらのエージェントかを知らず、spec の値だけを見て動作する。
"""

import asyncio
from dataclasses import dataclass

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from app.agent.spec import AgentSpec
from app.agent.trace import TraceRecorder


@dataclass
class AgentRunResult:
    run_id: str
    stop_reason: str  # completed / failed / max_turns / inner_timeout / inactivity_timeout
    output: str | None = None
    num_turns: int | None = None
    cost_usd: float | None = None


def _build_options(spec: AgentSpec) -> ClaudeAgentOptions:
    options_kwargs: dict = dict(
        system_prompt=spec.system_prompt,
        mcp_servers={spec.mcp_label: spec.mcp_server},
        # tools: ロースター自体をこのエージェントのMCPツールのみに限定する（Bash/Read/Write等の
        # 組み込みツールを一切使わせない）。allowed_tools は権限面（確認省略対象）の指定であり、
        # tools を指定しない場合は既定で組み込みツール一式が使える状態になってしまうため必須。
        # agent-development.md「してはいけない操作はhooks/disallowed_toolsで強制する」に対応する
        # 構造的なガードレール（AGENT-01実機評価でBash/Readが使われた事象を受けて追加）
        tools=spec.allowed_tool_names,
        allowed_tools=spec.allowed_tool_names,
        max_turns=spec.max_turns,
    )
    if spec.hooks:
        options_kwargs["hooks"] = spec.hooks
    return ClaudeAgentOptions(**options_kwargs)


async def run_agent(
    prompt: str,
    spec: AgentSpec,
    *,
    scenario: str | None = None,
    trace: TraceRecorder | None = None,
) -> AgentRunResult:
    """エージェントを1回実行し、全メッセージをトレースに記録する。

    trace は jobs.py が run_id を先に確定させるために注入する（省略時は内部で生成）。
    直接 await しない — 起動は jobs.start_agent_job() 経由（外側タイムアウト込み）。
    """
    trace = trace or TraceRecorder(scenario=scenario)
    trace.record_input(prompt)
    result = AgentRunResult(run_id=trace.run_id, stop_reason="failed")

    try:
        # 内側タイムアウト: 実行全体の上限
        async with asyncio.timeout(spec.inner_timeout_s):
            stream = query(prompt=prompt, options=_build_options(spec)).__aiter__()
            while True:
                try:
                    # ハング検知: メッセージ間の無応答が inactivity_timeout_s を超えたら停止
                    message = await asyncio.wait_for(
                        stream.__anext__(), spec.inactivity_timeout_s
                    )
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    result.stop_reason = "inactivity_timeout"
                    trace.record_result(
                        "inactivity_timeout",
                        detail=f"{spec.inactivity_timeout_s}s 無応答",
                    )
                    return result

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            trace.record_decision(block.text)
                        elif isinstance(block, ToolUseBlock):
                            trace.record_tool_use(block.name, block.input)
                elif isinstance(message, UserMessage):
                    for block in getattr(message, "content", []) or []:
                        if isinstance(block, ToolResultBlock):
                            trace.record_observation(
                                tool_name="",
                                content=block.content,
                                is_error=block.is_error,
                            )
                elif isinstance(message, ResultMessage):
                    completed = not message.is_error
                    if message.num_turns and message.num_turns >= spec.max_turns:
                        result.stop_reason = "max_turns"
                    else:
                        result.stop_reason = "completed" if completed else "failed"
                    result.output = message.result
                    result.num_turns = message.num_turns
                    result.cost_usd = message.total_cost_usd
                    trace.record_result(
                        result.stop_reason,
                        num_turns=message.num_turns,
                        cost_usd=message.total_cost_usd,
                    )
    except TimeoutError:
        # 内側タイムアウト発火（agent-plan.md の強制停止）。記録してから返す。
        result.stop_reason = "inner_timeout"
        trace.record_result("inner_timeout", detail=f"{spec.inner_timeout_s}s 超過")
    return result
