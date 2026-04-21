# app/api/routes/notifications.py

from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentContext,
    get_notification_service,
)
from app.schemas.notification import NotificationList
from app.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])


@router.get("", response_model=NotificationList)
async def get_notifications(
    ctx: CurrentContext,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_list(
        user_id=ctx.user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )


@router.get("/unread-count")
async def get_unread_count(
    ctx: CurrentContext,
    service: NotificationService = Depends(get_notification_service),
):
    count = await service.get_unread_count(ctx.user.id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    ctx: CurrentContext,
    service: NotificationService = Depends(get_notification_service),
):
    success = await service.mark_as_read(notification_id, ctx.user.id)
    return {"success": success}


@router.patch("/read-all")
async def mark_all_as_read(
    ctx: CurrentContext,
    service: NotificationService = Depends(get_notification_service),
):
    count = await service.mark_all_as_read(ctx.user.id)
    return {"marked_count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    ctx: CurrentContext,
    service: NotificationService = Depends(get_notification_service),
):
    success = await service.delete(notification_id, ctx.user.id)
    return {"success": success}
