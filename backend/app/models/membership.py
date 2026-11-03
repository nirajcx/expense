from app.db import Base

from sqlalchemy import (
    String,
    DateTime,
    func,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime

from uuid import uuid4, UUID


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    role: Mapped[str] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "organization_id",
            name="uq_memberships_user_organization",
        ),
        CheckConstraint(
            "role IN ('owner', 'manager', 'employee')",
            name="ck_memberships_role",
        ),
    )
