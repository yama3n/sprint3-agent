from sqlalchemy import select

from app.models.agent_run import AgentRun
from app.repositories.base import BaseRepository


class AgentRunRepository(BaseRepository[AgentRun]):
    model = AgentRun

    async def get_latest_by_inquiry(self, inquiry_id: int) -> AgentRun | None:
        """GET /inquiries/{id}/agent-status が参照する『最新のagent_runs行』
        （agent-plan.md §2: started_atが最新の行のstage/progress_percent/status/error_messageを返す）"""
        result = await self.session.execute(
            select(AgentRun)
            .where(AgentRun.inquiry_id == inquiry_id)
            .order_by(AgentRun.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_inquiry(self, inquiry_id: int) -> list[AgentRun]:
        result = await self.session.execute(
            select(AgentRun)
            .where(AgentRun.inquiry_id == inquiry_id)
            .order_by(AgentRun.started_at)
        )
        return list(result.scalars().all())
