# DTOs at the boundary (API/app). Keep transport separate from domain/infra. SRP.

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class CreateUserDTO(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1)

class UserReadDTO(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # pydantic v2: support orm/entity mapping
