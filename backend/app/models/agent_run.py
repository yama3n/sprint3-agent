import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

_STAGES = "('uploading','extracting','structuring','reviewing','completed','failed','stopped')"


class ParsedDocument(Base):
    __tablename__ = "parsed_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("inquiry_files.id"), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    parsed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "agent_name IN ('agent01_extraction','agent02_verification')",
            name="ck_agent_runs_agent_name",
        ),
        CheckConstraint(
            "trigger IN ('new_upload','additional_upload')",
            name="ck_agent_runs_trigger",
        ),
        CheckConstraint(
            "status IN ('running','succeeded','failed','stopped')",
            name="ck_agent_runs_status",
        ),
        CheckConstraint(f"stage IN {_STAGES}", name="ck_agent_runs_stage"),
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_agent_runs_progress_percent",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="uploading")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tool_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    error_message: Mapped[str | None] = mapped_column(Text)


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    agent_run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    consumed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
