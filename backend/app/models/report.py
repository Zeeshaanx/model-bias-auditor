from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel
from app.models.enums import ReportFormat


class Report(TimestampedModel):
    """A rendered audit report in one output format."""

    __tablename__ = "reports"

    audit_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default=ReportFormat.JSON)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
