"""seed field_definitions (02-requirement A14+B8)

02-requirement.md 3章「4. 用語・固定項目の統一」準拠: A(case) 14項目・B(item) 8項目。
field_id は正本ドキュメントに明記が無いため実装時に定めた英語slug
（tests/integration/test_field_definitions_seed.py が命名の正）。
「エンジ会社」の field_id=engineering_company は agent-plan.md の表記に合わせた。

Revision ID: d47ffed47502
Revises: 7cbecbc6d800
Create Date: 2026-09-21 11:28:06.903103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d47ffed47502"
down_revision: Union[str, None] = "7cbecbc6d800"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

field_definitions = sa.table(
    "field_definitions",
    sa.column("field_id", sa.String),
    sa.column("scope", sa.String),
    sa.column("label", sa.String),
    sa.column("category", sa.String),
    sa.column("display_order", sa.Integer),
)

# 02-requirement.md 3章 A. 引合・案件全体の固定項目（14項目）
CASE_FIELDS = [
    ("requester", "依頼元企業", "auxiliary"),
    ("project_name", "案件名／プロジェクト名", "bootcamp_required"),
    ("inquiry_date", "引合日", "auxiliary"),
    ("quotation_deadline", "回答期限／見積期限", "auxiliary"),
    ("destination_country", "発注国／納入先国", "bootcamp_required"),
    ("usage", "用途", "bootcamp_required"),
    ("background", "案件背景／概要", "bootcamp_required"),
    ("end_user", "発注者／End User", "bootcamp_required"),
    ("engineering_company", "エンジニアリング会社", "bootcamp_required"),
    ("epc", "EPC", "bootcamp_required"),
    ("desired_delivery", "希望納期", "bootcamp_required"),
    ("quantity_scale", "数量感／案件規模", "bootcamp_required"),
    ("similar_case", "類似案件", "bootcamp_required"),
    ("market_condition", "市況", "bootcamp_required"),
]

# 02-requirement.md 3章 B. 品目ごとの固定項目（8項目）
ITEM_FIELDS = [
    ("pipe_making_method", "製管方法", "bootcamp_required"),
    ("item_usage", "用途", "bootcamp_required"),
    ("grade", "グレード", "bootcamp_required"),
    ("thread_type", "ネジ種", "bootcamp_required"),
    ("outer_diameter", "外径", "bootcamp_required"),
    ("wall_thickness", "肉厚", "bootcamp_required"),
    ("length", "長さ", "bootcamp_required"),
    ("quantity", "数量", "bootcamp_required"),
]


def upgrade() -> None:
    rows = [
        {
            "field_id": field_id,
            "scope": "case",
            "label": label,
            "category": category,
            "display_order": order,
        }
        for order, (field_id, label, category) in enumerate(CASE_FIELDS, start=1)
    ] + [
        {
            "field_id": field_id,
            "scope": "item",
            "label": label,
            "category": category,
            "display_order": order,
        }
        for order, (field_id, label, category) in enumerate(ITEM_FIELDS, start=1)
    ]
    op.bulk_insert(field_definitions, rows)


def downgrade() -> None:
    all_field_ids = [f[0] for f in CASE_FIELDS] + [f[0] for f in ITEM_FIELDS]
    op.execute(
        field_definitions.delete().where(
            field_definitions.c.field_id.in_(all_field_ids)
        )
    )
