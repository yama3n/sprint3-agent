import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.agent_run import AgentRun, ExtractionResult, ParsedDocument
from app.models.export import Export
from app.models.field import FieldCandidate, InquiryField, InquiryItemField
from app.models.inquiry import Inquiry, InquiryFile, InquiryItem, InquiryNote
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.export_repository import ExportRepository
from app.repositories.extraction_result_repository import ExtractionResultRepository
from app.repositories.field_candidate_repository import FieldCandidateRepository
from app.repositories.field_definition_repository import FieldDefinitionRepository
from app.repositories.inquiry_field_repository import InquiryFieldRepository
from app.repositories.inquiry_file_repository import InquiryFileRepository
from app.repositories.inquiry_item_field_repository import InquiryItemFieldRepository
from app.repositories.inquiry_item_repository import InquiryItemRepository
from app.repositories.inquiry_note_repository import InquiryNoteRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.repositories.parsed_document_repository import ParsedDocumentRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def inquiry(db_session: AsyncSession) -> Inquiry:
    repo = InquiryRepository(db_session)
    obj = await repo.add(Inquiry(inquiry_code="INQ-TEST-REPO-0001", status="draft"))
    await db_session.flush()
    return obj


async def test_inquiry_file_repository_list_by_inquiry(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    repo = InquiryFileRepository(db_session)
    await repo.add(
        InquiryFile(
            inquiry_id=inquiry.id,
            file_name="order.xlsx",
            file_type="xlsx",
            storage_path="/x",
        )
    )
    await db_session.flush()

    files = await repo.list_by_inquiry(inquiry.id)
    assert len(files) == 1
    assert files[0].file_name == "order.xlsx"


async def test_inquiry_item_repository_list_by_inquiry_ordered(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    repo = InquiryItemRepository(db_session)
    await repo.add(InquiryItem(inquiry_id=inquiry.id, item_no=2))
    await repo.add(InquiryItem(inquiry_id=inquiry.id, item_no=1))
    await db_session.flush()

    items = await repo.list_by_inquiry(inquiry.id)
    assert [i.item_no for i in items] == [1, 2]


async def test_inquiry_field_repository(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    field_def_repo = FieldDefinitionRepository(db_session)
    field_def = (await field_def_repo.list_by_scope("case"))[0]

    repo = InquiryFieldRepository(db_session)
    await repo.add(
        InquiryField(
            inquiry_id=inquiry.id, field_definition_id=field_def.id, status="review"
        )
    )
    await db_session.flush()

    by_inquiry = await repo.list_by_inquiry(inquiry.id)
    assert len(by_inquiry) == 1

    found = await repo.get_by_inquiry_and_field(inquiry.id, field_def.id)
    assert found is not None
    missing = await repo.get_by_inquiry_and_field(inquiry.id, field_def.id + 999)
    assert missing is None


async def test_inquiry_item_field_repository(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    field_def_repo = FieldDefinitionRepository(db_session)
    field_def = (await field_def_repo.list_by_scope("item"))[0]
    item = await InquiryItemRepository(db_session).add(
        InquiryItem(inquiry_id=inquiry.id, item_no=1)
    )
    await db_session.flush()

    repo = InquiryItemFieldRepository(db_session)
    await repo.add(
        InquiryItemField(
            inquiry_item_id=item.id, field_definition_id=field_def.id, status="review"
        )
    )
    await db_session.flush()

    by_item = await repo.list_by_inquiry_item(item.id)
    assert len(by_item) == 1

    found = await repo.get_by_item_and_field(item.id, field_def.id)
    assert found is not None


async def test_field_candidate_repository(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    field_def = (await FieldDefinitionRepository(db_session).list_by_scope("case"))[0]
    inquiry_field = await InquiryFieldRepository(db_session).add(
        InquiryField(
            inquiry_id=inquiry.id, field_definition_id=field_def.id, status="review"
        )
    )
    await db_session.flush()

    repo = FieldCandidateRepository(db_session)
    await repo.add(
        FieldCandidate(
            inquiry_field_id=inquiry_field.id,
            value="ノルウェー",
            source_type="pdf",
            source_file="見積依頼書.pdf",
            source_location="p.1",
        )
    )
    await db_session.flush()

    candidates = await repo.list_by_inquiry_field(inquiry_field.id)
    assert len(candidates) == 1
    assert candidates[0].value == "ノルウェー"

    empty = await repo.list_by_inquiry_item_field(999999)
    assert empty == []


async def test_inquiry_note_repository(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    repo = InquiryNoteRepository(db_session)
    await repo.add(
        InquiryNote(inquiry_id=inquiry.id, scope="case", content="特記事項テスト")
    )
    await db_session.flush()

    notes = await repo.list_by_inquiry(inquiry.id)
    assert len(notes) == 1


async def test_export_repository(db_session: AsyncSession, inquiry: Inquiry) -> None:
    repo = ExportRepository(db_session)
    await repo.add(
        Export(
            inquiry_id=inquiry.id,
            format="excel",
            state="draft",
            file_name="INQ-TEST-REPO-0001_draft.xlsx",
            storage_path="/exports/x.xlsx",
        )
    )
    await db_session.flush()

    exports = await repo.list_by_inquiry(inquiry.id)
    assert len(exports) == 1


async def test_agent_run_repository_get_latest(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    repo = AgentRunRepository(db_session)
    older = AgentRun(
        inquiry_id=inquiry.id,
        agent_name="agent01_extraction",
        trigger="new_upload",
        status="succeeded",
        stage="completed",
        started_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    )
    newer = AgentRun(
        inquiry_id=inquiry.id,
        agent_name="agent02_verification",
        trigger="new_upload",
        status="running",
        stage="structuring",
        started_at=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
    )
    await repo.add(older)
    await repo.add(newer)
    await db_session.flush()

    latest = await repo.get_latest_by_inquiry(inquiry.id)
    assert latest is not None
    assert latest.agent_name == "agent02_verification"

    all_runs = await repo.list_by_inquiry(inquiry.id)
    assert len(all_runs) == 2


async def test_extraction_result_repository_unconsumed(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    run = await AgentRunRepository(db_session).add(
        AgentRun(
            inquiry_id=inquiry.id,
            agent_name="agent01_extraction",
            trigger="new_upload",
            status="succeeded",
            stage="completed",
        )
    )
    await db_session.flush()

    repo = ExtractionResultRepository(db_session)
    await repo.add(
        ExtractionResult(
            inquiry_id=inquiry.id, agent_run_id=run.id, payload={"case_fields": {}}
        )
    )
    await db_session.flush()

    unconsumed = await repo.get_unconsumed_by_inquiry(inquiry.id)
    assert unconsumed is not None
    assert unconsumed.consumed_at is None


async def test_parsed_document_repository(
    db_session: AsyncSession, inquiry: Inquiry
) -> None:
    file = await InquiryFileRepository(db_session).add(
        InquiryFile(
            inquiry_id=inquiry.id,
            file_name="a.pdf",
            file_type="pdf",
            storage_path="/a.pdf",
        )
    )
    await db_session.flush()

    repo = ParsedDocumentRepository(db_session)
    await repo.add(ParsedDocument(file_id=file.id, content={"pages": []}))
    await db_session.flush()

    found = await repo.get_by_file(file.id)
    assert found is not None
