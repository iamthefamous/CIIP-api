from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.ciip_api.schemas.opportunities import OpportunityStatus


class ModerationAction(BaseModel):
    opportunity_id: UUID
    note: Optional[str]


class ModerationQueueItem(BaseModel):
    id: UUID
    opportunity_id: UUID
    status: OpportunityStatus
    reviewed_by: Optional[UUID]
    note: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
