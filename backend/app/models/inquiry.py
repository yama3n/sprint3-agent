import datetime

from sqlalchemy import (
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


class Inquiry(Base):
    __tablename__ = "inquiries"
    __table_args__ = (
        CheckConstraint("status IN ('draft','final')", name="ck_inquiries_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    requester: Mapped[str | None] = mapped_column(String(255))
    project_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    requested_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InquiryFile(Base):
    __tablename__ = "inquiry_files"
    __table_args__ = (
        CheckConstraint(
            "file_type IN ('xlsx','pdf','eml')", name="ck_inquiry_files_type"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InquiryItem(Base):
    __tablename__ = "inquiry_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    item_no: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InquiryNote(Base):
    __tablename__ = "inquiry_notes"
    __table_args__ = (
        CheckConstraint("scope IN ('case','item')", name="ck_inquiry_notes_scope"),
        CheckConstraint(
            "source_type IS NULL OR source_type IN ('pdf','excel','eml','web')",
            name="ck_inquiry_notes_source_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    inquiry_item_id: Mapped[int | None] = mapped_column(ForeignKey("inquiry_items.id"))
    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(10))
    source_file: Mapped[str | None] = mapped_column(String(255))
    source_location: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
