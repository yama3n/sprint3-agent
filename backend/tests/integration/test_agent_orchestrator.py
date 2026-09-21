from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import delete

from app.agent.agent02 import state as agent02_state
from app.core.db import AsyncSessionLocal
from app.models.agent_run import AgentRun, ExtractionResult
from app.models.inquiry import Inquiry
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.extraction_result_repository import ExtractionResultRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.services import agent_orchestrator


async def test_orchestrator_marks_the_handoff_payload_consumed(monkeypatch) -> None:
    async with AsyncSessionLocal() as session:
        inquiry = await InquiryRepository(session).add(
            Inquiry(inquiry_code=f"INQ-ORCH-{uuid4().hex[:8]}", status="draft")
        )
        await session.flush()
        run1 = await AgentRunRepository(session).add(
            AgentRun(
                inquiry_id=inquiry.id,
                agent_name="agent01_extraction",
                trigger="new_upload",
                status="succeeded",
                stage="completed",
                progress_percent=55,
            )
        )
        extraction = await ExtractionResultRepository(session).add(
            ExtractionResult(
                inquiry_id=inquiry.id,
                agent_run_id=run1.id,
                payload={
                    "inquiry_id": inquiry.id,
                    "case_fields": {},
                    "item_fields": {},
                    "case_notes": [{"content": "案件注記"}],
                    "item_notes": {"1": [{"content": "品目注記"}]},
                },
            )
        )
        await session.commit()
        inquiry_id, run1_id, extraction_id = inquiry.id, run1.id, extraction.id

    run_ids = iter(["agent01-job", "agent02-job"])
    monkeypatch.setattr(
        agent_orchestrator.jobs,
        "start_agent_job",
        lambda *args, **kwargs: next(run_ids),
    )
    monkeypatch.setattr(
        agent_orchestrator,
        "_await_job",
        lambda run_id: _completed_job(),
    )

    await agent_orchestrator._orchestrate(
        inquiry_id, run1_id, [], trigger="new_upload"
    )

    seeded_state = agent02_state.get_state(inquiry_id)
    assert seeded_state.case_notes == [{"content": "案件注記"}]
    assert seeded_state.item_notes == {1: [{"content": "品目注記"}]}

    async with AsyncSessionLocal() as session:
        consumed = await session.get(ExtractionResult, extraction_id)
        assert consumed.consumed_at is not None
        runs = await AgentRunRepository(session).list_by_inquiry(inquiry_id)
        assert runs[0].status == "succeeded"
        assert runs[0].stage == "completed"
        assert runs[1].status == "running"
        assert runs[1].stage == "structuring"
        await session.execute(
            delete(ExtractionResult).where(ExtractionResult.inquiry_id == inquiry_id)
        )
        await session.execute(
            delete(AgentRun).where(AgentRun.inquiry_id == inquiry_id)
        )
        await session.execute(delete(Inquiry).where(Inquiry.id == inquiry_id))
        await session.commit()
    agent02_state.clear_state(inquiry_id)


async def _completed_job():
    return SimpleNamespace(status="completed")
