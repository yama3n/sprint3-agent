import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent01.schema import CASE_FIELD_IDS, ITEM_FIELD_IDS
from app.core.db import AsyncSessionLocal
from app.repositories.field_definition_repository import FieldDefinitionRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


async def test_case_field_ids_match_db_seed(db_session: AsyncSession) -> None:
    repo = FieldDefinitionRepository(db_session)
    db_ids = [f.field_id for f in await repo.list_by_scope("case")]
    assert CASE_FIELD_IDS == db_ids


async def test_item_field_ids_match_db_seed(db_session: AsyncSession) -> None:
    repo = FieldDefinitionRepository(db_session)
    db_ids = [f.field_id for f in await repo.list_by_scope("item")]
    assert ITEM_FIELD_IDS == db_ids
