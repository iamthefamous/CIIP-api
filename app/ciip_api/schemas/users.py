from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    user = "user"
    institution = "institution"
    moderator = "moderator"
    admin = "admin"


class AudienceType(str, Enum):
    high_schoolers = "high_schoolers"
    university_students = "university_students"
    general_public = "general_public"


class UserContext(BaseModel):
    id: str
    email: Optional[str]
    role: str


class UserUpsert(BaseModel):
    full_name: Optional[str]
    audience_type: Optional[AudienceType]


class UserOut(BaseModel):
    id: UUID
    email: Optional[EmailStr]
    full_name: Optional[str]
    role: UserRole
    audience_type: Optional[AudienceType]
    created_at: datetime
    updated_at: datetime
