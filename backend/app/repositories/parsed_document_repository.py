from sqlalchemy import select

from app.models.agent_run import ParsedDocument
from app.repositories.base import BaseRepository


class ParsedDocumentRepository(BaseRepository[ParsedDocument]):
    model = ParsedDocument

    async def get_by_file(self, file_id: int) -> ParsedDocument | None:
        result = await self.session.execute(
            select(ParsedDocument).where(ParsedDocument.file_id == file_id)
        )
        return result.scalar_one_or_none()
