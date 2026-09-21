import datetime

from sqlalchemy import (
    Boolean,
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

_REASON_TYPES = "('missing','conflict','ambiguous','multiple_candidates','parse_error')"
_STATUSES = "('ok','review')"
_CONFIRMED_BY = "('ai','web','user')"


class FieldDefinition(Base):
    __tablename__ = "field_definitions"
    __table_args__ = (
        CheckConstraint("scope IN ('case','item')", name="ck_field_definitions_scope"),
        CheckConstraint(
            "category IN ('bootcamp_required','auxiliary')",
            name="ck_field_definitions_category",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class InquiryField(Base):
    __tablename__ = "inquiry_fields"
    __table_args__ = (
        CheckConstraint(f"status IN {_STATUSES}", name="ck_inquiry_fields_status"),
        CheckConstraint(
            f"reason_type IS NULL OR reason_type IN {_REASON_TYPES}",
            name="ck_inquiry_fields_reason_type",
        ),
        CheckConstraint(
            f"confirmed_by IS NULL OR confirmed_by IN {_CONFIRMED_BY}",
            name="ck_inquiry_fields_confirmed_by",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    field_definition_id: Mapped[int] = mapped_column(
        ForeignKey("field_definitions.id"), nullable=False
    )
    value: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="review")
    reason_type: Mapped[str | None] = mapped_column(String(20))
    is_web_supplemented: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    confirmed_by: Mapped[str | None] = mapped_column(String(10))
    confirmed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InquiryItemField(Base):
    __tablename__ = "inquiry_item_fields"
    __table_args__ = (
        CheckConstraint(f"status IN {_STATUSES}", name="ck_inquiry_item_fields_status"),
        CheckConstraint(
            f"reason_type IS NULL OR reason_type IN {_REASON_TYPES}",
            name="ck_inquiry_item_fields_reason_type",
        ),
        CheckConstraint(
            f"confirmed_by IS NULL OR confirmed_by IN {_CONFIRMED_BY}",
            name="ck_inquiry_item_fields_confirmed_by",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_item_id: Mapped[int] = mapped_column(
        ForeignKey("inquiry_items.id"), nullable=False
    )
    field_definition_id: Mapped[int] = mapped_column(
        ForeignKey("field_definitions.id"), nullable=False
    )
    value: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="review")
    reason_type: Mapped[str | None] = mapped_column(String(20))
    is_web_supplemented: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    confirmed_by: Mapped[str | None] = mapped_column(String(10))
    confirmed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FieldCandidate(Base):
    __tablename__ = "field_candidates"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('pdf','excel','eml','web')",
            name="ck_field_candidates_source_type",
        ),
        CheckConstraint(
            "(inquiry_field_id IS NOT NULL AND inquiry_item_field_id IS NULL) OR "
            "(inquiry_field_id IS NULL AND inquiry_item_field_id IS NOT NULL)",
            name="ck_field_candidates_exactly_one_parent",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_field_id: Mapped[int | None] = mapped_column(
        ForeignKey("inquiry_fields.id")
    )
    inquiry_item_field_id: Mapped[int | None] = mapped_column(
        ForeignKey("inquiry_item_fields.id")
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(255))
    source_location: Mapped[str | None] = mapped_column(String(255))
    quoted_text: Mapped[str | None] = mapped_column(Text)
    web_url: Mapped[str | None] = mapped_column(String(500))
    web_source_name: Mapped[str | None] = mapped_column(String(255))
    web_referenced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    is_explicit_correction: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    superseded_value: Mapped[str | None] = mapped_column(Text)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
