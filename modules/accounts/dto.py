# DTOs at the boundary (API/app). Keep transport separate from domain/infra. SRP.

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict

class CreateUserDTO(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1)

class UserReadDTO(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    # old Pydantic v1 style
    # class Config:
    #    from_attributes = True  # pydantic v2: support orm/entity mapping
    
    # new Pydantic v2 style
    model_config = ConfigDict(from_attributes=True)
