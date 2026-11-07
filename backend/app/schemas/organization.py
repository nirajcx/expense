from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrganizationCreate(BaseModel):

    @field_validator("name", mode="before")
    @classmethod
    def strip_full_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    name: str = Field(min_length=1, max_length=100)


class OrganizationRead(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=100)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
