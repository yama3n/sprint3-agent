from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_run import AgentRun, ExtractionResult, ParsedDocument
from app.models.export import Export
from app.models.field import FieldCandidate, InquiryField, InquiryItemField
from app.models.inquiry import Inquiry, InquiryFile, InquiryItem, InquiryNote


class InquiryDeletionRepository:
    """引合を外部キーの依存順に削除するData Access境界。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete(self, inquiry_id: int) -> list[str]:
        file_paths = list(
            (
                await self.session.execute(
                    select(InquiryFile.storage_path).where(
                        InquiryFile.inquiry_id == inquiry_id
                    )
                )
            ).scalars()
        )
        file_paths.extend(
            (
                await self.session.execute(
                    select(Export.storage_path).where(Export.inquiry_id == inquiry_id)
                )
            ).scalars()
        )

        file_ids = select(InquiryFile.id).where(InquiryFile.inquiry_id == inquiry_id)
        item_ids = select(InquiryItem.id).where(InquiryItem.inquiry_id == inquiry_id)
        case_field_ids = select(InquiryField.id).where(
            InquiryField.inquiry_id == inquiry_id
        )
        item_field_ids = select(InquiryItemField.id).where(
            InquiryItemField.inquiry_item_id.in_(item_ids)
        )

        await self.session.execute(
            delete(FieldCandidate).where(
                or_(
                    FieldCandidate.inquiry_field_id.in_(case_field_ids),
                    FieldCandidate.inquiry_item_field_id.in_(item_field_ids),
                )
            )
        )
        await self.session.execute(
            delete(ParsedDocument).where(ParsedDocument.file_id.in_(file_ids))
        )
        await self.session.execute(
            delete(ExtractionResult).where(ExtractionResult.inquiry_id == inquiry_id)
        )
        await self.session.execute(
            delete(InquiryNote).where(InquiryNote.inquiry_id == inquiry_id)
        )
        await self.session.execute(
            delete(InquiryItemField).where(
                InquiryItemField.inquiry_item_id.in_(item_ids)
            )
        )
        await self.session.execute(
            delete(InquiryField).where(InquiryField.inquiry_id == inquiry_id)
        )
        await self.session.execute(delete(Export).where(Export.inquiry_id == inquiry_id))
        await self.session.execute(
            delete(AgentRun).where(AgentRun.inquiry_id == inquiry_id)
        )
        await self.session.execute(
            delete(InquiryItem).where(InquiryItem.inquiry_id == inquiry_id)
        )
        await self.session.execute(
            delete(InquiryFile).where(InquiryFile.inquiry_id == inquiry_id)
        )
        await self.session.execute(delete(Inquiry).where(Inquiry.id == inquiry_id))
        return file_paths
