from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel
from app.models.enums import AuditStatus


class Audit(TimestampedModel):
    """One bias audit run against a single target."""

    __tablename__ = "audits"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    probe_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evaluator_id: Mapped[str] = mapped_column(String(100), nullable=False, default="composite-disparity")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AuditStatus.PENDING, index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
