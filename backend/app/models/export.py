import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Export(Base):
    __tablename__ = "exports"
    __table_args__ = (
        CheckConstraint("format IN ('excel','word','pdf')", name="ck_exports_format"),
        CheckConstraint("state IN ('draft','final')", name="ck_exports_state"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id"), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    state: Mapped[str] = mapped_column(String(10), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
