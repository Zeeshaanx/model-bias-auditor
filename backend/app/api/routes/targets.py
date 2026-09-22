from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.target import TargetCreate, TargetRead, TargetUpdate
from app.services import target as target_service

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
async def create_target(payload: TargetCreate, session: AsyncSession = Depends(get_session)) -> TargetRead:
    return TargetRead.model_validate(await target_service.create_target(session, payload))


@router.get("", response_model=list[TargetRead])
async def list_targets(session: AsyncSession = Depends(get_session)) -> list[TargetRead]:
    return [TargetRead.model_validate(item) for item in await target_service.list_targets(session)]


@router.get("/{target_id}", response_model=TargetRead)
async def get_target(target_id: str, session: AsyncSession = Depends(get_session)) -> TargetRead:
    target = await target_service.get_target(session, target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return TargetRead.model_validate(target)


@router.patch("/{target_id}", response_model=TargetRead)
async def update_target(target_id: str, payload: TargetUpdate, session: AsyncSession = Depends(get_session)) -> TargetRead:
    target = await target_service.get_target(session, target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return TargetRead.model_validate(await target_service.update_target(session, target, payload))


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id: str, session: AsyncSession = Depends(get_session)) -> None:
    target = await target_service.get_target(session, target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    await target_service.delete_target(session, target)
