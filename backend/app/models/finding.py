from typing import Any

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel
from app.models.enums import Severity


class Finding(TimestampedModel):
    """A measured disparity between demographic groups for one probe."""

    __tablename__ = "findings"

    audit_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    probe_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    probe_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    attribute: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    evaluator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=Severity.INFO, index=True)
    disparity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Number of groups actually compared. A gap is the spread across arms, so it tends to
    # widen with more arms: findings from probes with different arm counts are not directly
    # comparable, and storing this is what makes that checkable after the fact.
    arm_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # True when the responses were too short for the per-100-token rates to be stable.
    low_signal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
