from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel


class ProbeResult(TimestampedModel):
    """Raw evidence for one probe: the paired prompts sent and the responses received."""

    __tablename__ = "probe_results"

    audit_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    probe_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    attribute: Mapped[str] = mapped_column(String(50), nullable=False)
    prompts: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    responses: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    errors: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
