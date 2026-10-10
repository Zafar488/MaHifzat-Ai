"""Authentication and authorization schemas."""
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    PATIENT = "patient"
    LHW = "lhw"              # Lady Health Worker
    CLINICIAN = "clinician"
    ADMIN = "admin"


class TokenPayload(BaseModel):
    sub: str              # user_id
    role: UserRole
    exp: Optional[int] = None
    token_version: int = 0


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.PATIENT
    full_name: Optional[str] = None


class UserInDB(BaseModel):
    user_id: str
    username: str
    hashed_password: str
    role: UserRole
    full_name: Optional[str] = None
    created_at: datetime
    is_active: bool = True
