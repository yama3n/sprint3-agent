import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.repositories.field_definition_repository import FieldDefinitionRepository

# 02-requirement.md 3章「4. 用語・固定項目の統一」準拠:
# A(case) 14項目・B(item) 8項目。field_id は正本ドキュメントに明記が無いため実装時に定めた
# 英語slug（このテストが命名の正）。エンジ会社→engineering_companyはagent-plan.mdの表記に合わせた。
EXPECTED_CASE_FIELD_IDS = [
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
EXPECTED_ITEM_FIELD_IDS = [
    "pipe_making_method",
    "item_usage",
    "grade",
    "thread_type",
    "outer_diameter",
    "wall_thickness",
    "length",
    "quantity",
]


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


async def test_case_fields_seeded(db_session: AsyncSession) -> None:
    repo = FieldDefinitionRepository(db_session)
    case_fields = await repo.list_by_scope("case")

    assert [f.field_id for f in case_fields] == EXPECTED_CASE_FIELD_IDS
    assert all(f.category in ("bootcamp_required", "auxiliary") for f in case_fields)


async def test_item_fields_seeded(db_session: AsyncSession) -> None:
    repo = FieldDefinitionRepository(db_session)
    item_fields = await repo.list_by_scope("item")

    assert [f.field_id for f in item_fields] == EXPECTED_ITEM_FIELD_IDS
    assert all(f.category == "bootcamp_required" for f in item_fields)


async def test_field_ids_are_globally_unique(db_session: AsyncSession) -> None:
    repo = FieldDefinitionRepository(db_session)
    all_fields = await repo.list()

    field_ids = [f.field_id for f in all_fields]
    assert len(field_ids) == len(set(field_ids))
    assert len(all_fields) == 22
