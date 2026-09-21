from sqlalchemy import select

from app.models.field import FieldDefinition
from app.repositories.base import BaseRepository


class FieldDefinitionRepository(BaseRepository[FieldDefinition]):
    model = FieldDefinition

    async def get_by_field_id(self, field_id: str) -> FieldDefinition | None:
        result = await self.session.execute(
            select(FieldDefinition).where(FieldDefinition.field_id == field_id)
        )
        return result.scalar_one_or_none()

    async def list_by_scope(self, scope: str) -> list[FieldDefinition]:
        result = await self.session.execute(
            select(FieldDefinition)
            .where(FieldDefinition.scope == scope)
            .order_by(FieldDefinition.display_order)
        )
        return list(result.scalars().all())
