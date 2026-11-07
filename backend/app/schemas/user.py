from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_full_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
