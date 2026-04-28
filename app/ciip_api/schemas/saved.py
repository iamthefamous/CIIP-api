from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class SavedCreate(BaseModel):
    opportunity_id: UUID


class SavedOpportunity(BaseModel):
    opportunity_id: UUID
    saved_at: datetime


class SavedList(BaseModel):
    total: int
    items: List[SavedOpportunity]
