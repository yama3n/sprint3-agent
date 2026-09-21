"""AGENT-01/AGENT-02が共有する固定項目ID一覧。

02-requirement.md 3章「4. 用語・固定項目の統一」準拠。field_id はDB側の唯一の正
（backend/alembic/versions/d47ffed47502_..._migration.py のシードデータ）と一致させる。
マイグレーションは履歴として凍結するため、ここに改めて正本を持つ
（tests/integration/test_field_definitions_seed.py が両者の一致を検証する）。
"""

CASE_FIELD_IDS: list[str] = [
    "requester",
    "project_name",
    "inquiry_date",
    "quotation_deadline",
    "destination_country",
    "usage",
    "background",
    "end_user",
    "engineering_company",
    "epc",
    "desired_delivery",
    "quantity_scale",
    "similar_case",
    "market_condition",
]

ITEM_FIELD_IDS: list[str] = [
    "pipe_making_method",
    "item_usage",
    "grade",
    "thread_type",
    "outer_diameter",
    "wall_thickness",
    "length",
    "quantity",
]

SOURCE_TYPES = ("pdf", "excel", "eml", "web")

# 日本語ラベル（02-requirement.md 3章の項目名）。システムプロンプトでfield_idを一字一句
# 指定するために使う（実機評価で、ラベルのみ渡すと"customer_name"のような推測field_idを
# 使ってしまう事象を確認したため、正確なIDをプロンプトへ明示する）
CASE_FIELD_LABELS: dict[str, str] = {
    "requester": "依頼元企業",
    "project_name": "案件名／プロジェクト名",
    "inquiry_date": "引合日",
    "quotation_deadline": "回答期限／見積期限",
    "destination_country": "発注国／納入先国",
    "usage": "用途",
    "background": "案件背景／概要",
    "end_user": "発注者／End User",
    "engineering_company": "エンジニアリング会社",
    "epc": "EPC",
    "desired_delivery": "希望納期",
    "quantity_scale": "数量感／案件規模",
    "similar_case": "類似案件",
    "market_condition": "市況",
}

ITEM_FIELD_LABELS: dict[str, str] = {
    "pipe_making_method": "製管方法",
    "item_usage": "用途",
    "grade": "グレード",
    "thread_type": "ネジ種",
    "outer_diameter": "外径",
    "wall_thickness": "肉厚",
    "length": "長さ",
    "quantity": "数量",
}
