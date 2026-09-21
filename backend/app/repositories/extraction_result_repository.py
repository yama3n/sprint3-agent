from sqlalchemy import select

from app.models.agent_run import ExtractionResult
from app.repositories.base import BaseRepository


class ExtractionResultRepository(BaseRepository[ExtractionResult]):
    model = ExtractionResult

    async def get_unconsumed_by_inquiry(
        self, inquiry_id: int
    ) -> ExtractionResult | None:
        """AGENT-02が消費する未処理のExtractionResult（consumed_at IS NULL）を取得する。"""
        result = await self.session.execute(
            select(ExtractionResult).where(
                ExtractionResult.inquiry_id == inquiry_id,
                ExtractionResult.consumed_at.is_(None),
            ).order_by(ExtractionResult.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()
