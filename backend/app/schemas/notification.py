from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: str = "info"
    category: str = "system"
    entity_type: str | None = None
    entity_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)


class NotificationRead(BaseModel):
    id: UUID
    title: str
    message: str
    type: str
    category: str
    entity_type: str | None
    entity_id: UUID | None
    is_read: bool
    metadata: dict = Field(
        default_factory=dict,
        validation_alias="metadata_",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class NotificationList(BaseModel):
    items: list[NotificationRead]
    unread_count: int
    total: int


class NotificationUpdate(BaseModel):
    is_read: bool = True
