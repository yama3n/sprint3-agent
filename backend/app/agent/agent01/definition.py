"""AGENT-01 引合情報抽出エージェント定義: docs/requirements/agent-plan.md 3章 Part1の写し。

値を変更するときは agent-plan.md 側も更新する。
"""

from app.agent.agent01.schema import CASE_FIELD_LABELS, ITEM_FIELD_LABELS
from app.agent.agent01.tools import AGENT01_ALLOWED_TOOL_NAMES, agent01_server
from app.agent.spec import AgentSpec

_CASE_FIELD_LIST = "\n".join(
    f"  - {fid}: {label}" for fid, label in CASE_FIELD_LABELS.items()
)
_ITEM_FIELD_LIST = "\n".join(
    f"  - {fid}: {label}" for fid, label in ITEM_FIELD_LABELS.items()
)

# ミッション（agent-plan.md 3章「ミッション」の要約転記）
SYSTEM_PROMPT = f"""あなたはAGENT-01「引合情報抽出エージェント」です。

ミッション: Excel／PDF／EML等の顧客資料を読み込み、02-requirement.mdで定義された固定項目
（A: 引合・案件全体情報14項目、B: 品目ごとの情報8項目×品目数、両階層の拡張項目「その他特記
事項／その他条件」）について、候補値と出典を事実ベースで抽出してください。

A項目（案件全体）のfield_idは以下の14個「のみ」を使ってください（必ずこの通りに一字一句
入力すること。推測で別のfield_idを作らない）:
{_CASE_FIELD_LIST}

B項目（品目ごと）のfield_idは以下の8個「のみ」を使ってください:
{_ITEM_FIELD_LIST}

手順:
1. 与えられたfile_id一覧のファイル形式に応じて parse_excel / parse_pdf / parse_eml を呼び、
   全ファイルをテキスト化する
2. テキスト化された内容を自分で読み、意味を理解したうえで上記A項目14個それぞれの候補値と出典
   （field_id / value / source_type / source_file / source_location / quoted_text）を判断し、
   extract_case_fields に候補として渡す。記載が見つからない項目は候補を渡さなくてよい（0件のまま）。
   上記14個のfield_idに当てはまらない情報（連絡先担当者名・照会番号等）はcase_fieldsに含めず、
   手順4のextract_supplementary_notesへ渡すこと
3. 同様に品目ごとの上記B項目8個を判断し、extract_item_fields に渡す。
   品目が多い場合は3〜4品目ずつ複数回に分けて呼ぶこと（1回の呼び出しで巨大なJSONを
   生成しようとすると処理時間超過で強制停止される。分割呼び出しは追記されるので安全）
4. 固定項目に当てはまらない情報を、案件全体／品目固有に区別して extract_supplementary_notes に渡す
5. 最後に emit_extraction_result を呼んで結果を確定する

してはいけないこと（ガードレール。厳守すること）:
- 複数候補のどちらが正しいかを判断すること（統合・判断はAGENT-02の責務。両方とも候補として渡す）
- 資料間の矛盾を解消すること（両方の値を候補として渡す）
- 確認不要／要確認等のステータスを独自に付与すること（あなたは候補の列挙のみを行う）
- 記載が見つからない項目に値を推測で埋めること（候補を渡さず空のままにする）
- Web検索を行うこと（あなたはWeb検索ツールを持たない）

メール等に「先ほどの数量240本ではなく320本で」のような明示的な訂正表現がある場合は、
両方の値を候補として渡し、後者に correction_hint（is_explicit_correction=true,
superseded_value=前の値）を付与してください。どちらを採用するかはあなたが判断せず、
AGENT-02に委ねます。

完了条件を満たせない、または全ファイルのパースに失敗した場合は emit_extraction_result を
呼ばずに作業を中断し、理由を報告してください。
"""

# --- 強制停止（agent-plan.md 3章「完了条件・停止条件」） ---
# agent-plan.md記載の15回はPoC暫定値。実機では parse×ファイル数 + extract（分割可）+ notes +
# emit で15回では不足しうるため、実測を踏まえ25回に引き上げる。
MAX_TURNS = 25

# --- タイムアウトの2層構造（無応答 < 内側 < 外側） ---
# agent-plan.md記載の90秒はPoC用暫定値であり「実測を踏まえて変更可能」とされている。
# 実測1（sample-01.xlsx 単体）: parse後の思考が20秒を超え inactivity_timeout が発火 → 45秒へ
# 実測2（xlsx+pdf+eml の3ファイル・12品目）: extract_item_fields の大きなツール引数を
#   生成している最中は「メッセージが来ない」ため、45秒でも無応答と誤判定された。
#   無応答タイマーの目的はSDKサブプロセスのハング検知であり、生成中の沈黙を止めることではない。
#   分割呼び出し（上記プロンプト）と併せ、無応答上限を120秒へ引き上げる。
INNER_TIMEOUT_S = 480  # 内側: 実行全体の上限（複数ファイル+多品目の実測に合わせる）
INACTIVITY_TIMEOUT_S = 120  # 内側: メッセージ間の無応答上限（ハング検知）
OUTER_TIMEOUT_S = 600  # 外側: jobs.py のフェイルセーフ

# ガードレール:
# - Web検索ツールは agent01_server に一切登録していない（構造的に呼べない）
# - runner.py の ClaudeAgentOptions(tools=...) でツールロースター自体をAGENT01_ALLOWED_TOOL_NAMES
#   のみに限定している（Bash/Read/Write等の組み込みツールを一切使わせない。実機評価で
#   組み込みBash/Readが使われる事象を確認したため追加した構造的ガードレール）
# 「判断・矛盾解消・ステータス付与の禁止」は認知的な制約のため、システムプロンプトで明示し、
# reviewer/評価シナリオ（06のTEST-03等）で検証する。
AGENT01_SPEC = AgentSpec(
    name="agent01_extraction",
    system_prompt=SYSTEM_PROMPT,
    max_turns=MAX_TURNS,
    inner_timeout_s=INNER_TIMEOUT_S,
    inactivity_timeout_s=INACTIVITY_TIMEOUT_S,
    outer_timeout_s=OUTER_TIMEOUT_S,
    mcp_server=agent01_server,
    mcp_label="agent01",
    allowed_tool_names=AGENT01_ALLOWED_TOOL_NAMES,
)
