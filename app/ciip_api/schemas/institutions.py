from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class InstitutionCreate(BaseModel):
    name: str
    description: Optional[str]
    website: Optional[HttpUrl]


class InstitutionOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    website: Optional[str]
    is_verified: bool
    owner_user_id: UUID
    created_at: datetime
    updated_at: datetime
