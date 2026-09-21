from sqlalchemy import select

from app.models.field import FieldDefinition
from app.repositories.base import BaseRepository


class FieldDefinitionRepository(BaseRepository[FieldDefinition]):
    model = FieldDefinition

    async def list_by_scope(self, scope: str) -> list[FieldDefinition]:
        result = await self.session.execute(
            select(FieldDefinition)
            .where(FieldDefinition.scope == scope)
            .order_by(FieldDefinition.display_order)
        )
        return list(result.scalars().all())
