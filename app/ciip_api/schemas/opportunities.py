from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.ciip_api.schemas.users import AudienceType


class OpportunityType(str, Enum):
    internship = "internship"
    job = "job"
    course = "course"
    volunteer = "volunteer"
    event = "event"


class OpportunityStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class OpportunityCreate(BaseModel):
    title: str
    description: str
    opportunity_type: OpportunityType
    category_id: UUID
    institution_id: UUID
    deadline: Optional[date] = None
    location: Optional[str] = None
    url: Optional[str] = None
    audiences: List[AudienceType]
    generate_ai: bool = False


class OpportunityOut(BaseModel):
    id: UUID
    title: str
    description: str
    opportunity_type: OpportunityType
    category_id: UUID
    institution_id: UUID
    submitted_by: UUID
    status: OpportunityStatus
    deadline: Optional[date]
    location: Optional[str]
    url: Optional[str]
    ai_tags: Optional[list]
    ai_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    audiences: List[AudienceType]


class OpportunityList(BaseModel):
    total: int
    items: List[OpportunityOut]
