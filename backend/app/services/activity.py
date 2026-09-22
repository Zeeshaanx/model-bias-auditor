from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def record(session: AsyncSession, entity_type: str, entity_id: str, action: str, detail: dict[str, Any] | None = None) -> None:
    session.add(AuditLog(entity_type=entity_type, entity_id=entity_id, action=action, detail=detail or {}))
    await session.flush()
