from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    slug: str


class CategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime
