from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TimestampedModel
from app.models.enums import TargetProvider


class Target(TimestampedModel):
    """An AI system under audit."""

    __tablename__ = "targets"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default=TargetProvider.MOCK)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False, default="mock-model")
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
