"""エージェント定義: docs/requirements/agent-plan.md Part 1 に対応する。

このファイルの値は設計書（agent-plan.md）の写しであり、変更するときは agent-plan.md 側も更新する。
Foundation段階（Slice 0-7）で作られたAGENT-01/AGENT-02共通のスケルトン値。
Direct Build Phase 5/6 で AGENT-01（app/agent/agent01/）・AGENT-02（app/agent/agent02/）
それぞれ専用の AgentSpec に分離した。このファイルは Slice 0-7 の疎通確認用 ping ツールの
スケルトンとして残す（PING_AGENT_SPEC、smoke test 用）。
"""

from app.agent.spec import AgentSpec
from app.agent.tools import ALLOWED_TOOL_NAMES, agent_server

# ミッション（agent-plan.md「1. エージェント一覧」を反映。build-loopのエージェントスライスが
# AGENT-01/AGENT-02それぞれのシステムプロンプトに具体化する）
SYSTEM_PROMPT = """あなたは引合書整理エージェントの一部として動作します。
Excel/PDF/EMLの顧客資料から固定項目（引合・案件全体情報、品目情報）の候補値と出典を
事実ベースで抽出、または複数資料を横断して検証・統合し、確認が必要な項目を要確認として
検知します。判断できない矛盾は自動的にどちらかを正とせず、両方の値と出典を保持してください。
完了条件を満たせない、または失敗と判断したら作業を中断し、理由を報告してください。
"""

# --- 強制停止（agent-plan.md の「完了条件・停止条件」の強制停止行に対応） ---
# agent-plan.md: AGENT-01 = ツール呼び出し数15回/タイムアウト90秒、
#                AGENT-02 = ツール呼び出し数15回/タイムアウト120秒（いずれも【仮説・PoC用暫定値】）
# Foundationのスケルトンでは、より長いAGENT-02側の値を暫定採用する。
# build-loopのエージェントスライスでAGENT-01/AGENT-02それぞれの definition に分離する。
MAX_TURNS = (
    15  # 最大ターン数（agent-plan.md の最大ツール呼び出し数15回に対応、SDKに渡す）
)

# --- タイムアウトの2層構造（必ず 内側 < 外側 を守る） ---
# 内側 = エージェント自身の停止条件。発火したらトレースに記録して整然と終了する。
# 外側 = ジョブ層（jobs.py）のフェイルセーフ。内側がハング等で発火できないときの最後の砦。
INNER_TIMEOUT_S = (
    120  # 内側: エージェント実行全体の上限（agent-plan.md AGENT-02のタイムアウト値）
)
INACTIVITY_TIMEOUT_S = 30  # 内側: メッセージ間の無応答上限（ハング検知）
OUTER_TIMEOUT_S = 180  # 外側: jobs.py が run_agent() 全体に掛ける上限

assert INACTIVITY_TIMEOUT_S < INNER_TIMEOUT_S < OUTER_TIMEOUT_S, (
    "タイムアウトは 無応答 < 内側 < 外側 の順でなければならない。"
    "外側が先に発火すると、トレースに停止理由を記録できないまま実行が破棄される。"
)

# ガードレール（agent-plan.md の「ガードレール」に対応。build-loopのエージェントスライスが
# AGENT-01/AGENT-02それぞれの「してはいけない操作」に基づいて具体化する。
# 例: AGENT-01はWeb検索ツールを持たない、AGENT-02は確定済み状態への書き込み権限を持たない）
BLOCKED_PATTERNS: list[str] = []

# Slice 0-7 疎通確認用（ping ツールのみ）。app.agent.spec.AgentSpec 化した参照実装。
PING_AGENT_SPEC = AgentSpec(
    name="ping",
    system_prompt=SYSTEM_PROMPT,
    max_turns=MAX_TURNS,
    inner_timeout_s=INNER_TIMEOUT_S,
    inactivity_timeout_s=INACTIVITY_TIMEOUT_S,
    outer_timeout_s=OUTER_TIMEOUT_S,
    mcp_server=agent_server,
    mcp_label="app",
    allowed_tool_names=ALLOWED_TOOL_NAMES,
)
