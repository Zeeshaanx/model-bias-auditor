from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.target import Target
from app.schemas.target import TargetCreate, TargetUpdate
from app.services import activity


async def create_target(session: AsyncSession, payload: TargetCreate) -> Target:
    target = Target(
        name=payload.name,
        description=payload.description,
        provider=str(payload.provider),
        model_name=payload.model_name,
        configuration=payload.configuration,
    )
    session.add(target)
    await session.flush()
    await activity.record(session, "target", target.id, "created", {"provider": target.provider})
    await session.commit()
    await session.refresh(target)
    return target


async def list_targets(session: AsyncSession) -> list[Target]:
    result = await session.execute(select(Target).order_by(Target.created_at.desc()))
    return list(result.scalars().all())


async def get_target(session: AsyncSession, target_id: str) -> Target | None:
    return await session.get(Target, target_id)


async def update_target(session: AsyncSession, target: Target, payload: TargetUpdate) -> Target:
    data = payload.model_dump(exclude_unset=True)
    if "provider" in data and data["provider"] is not None:
        data["provider"] = str(data["provider"])
    for field, value in data.items():
        if value is not None:
            setattr(target, field, value)
    await activity.record(session, "target", target.id, "updated", {"fields": sorted(data)})
    await session.commit()
    await session.refresh(target)
    return target


async def delete_target(session: AsyncSession, target: Target) -> None:
    await activity.record(session, "target", target.id, "deleted", {})
    await session.delete(target)
    await session.commit()
