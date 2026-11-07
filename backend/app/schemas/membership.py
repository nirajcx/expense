from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from typing import Literal


class MembershipCreate(BaseModel):
    user_id: UUID
    role: Literal["manager", "employee"]


class MembershipRead(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: Literal["owner", "manager", "employee"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
