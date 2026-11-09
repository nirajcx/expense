from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.dependencies import get_current_user, require_organization_owner
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.schemas.membership import MembershipCreate, MembershipRead

from uuid import UUID

from fastapi import HTTPException

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OwnerDep = Annotated[
    Membership,
    Depends(require_organization_owner),
]


@router.post(
    "",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    payload: OrganizationCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    organization = Organization(name=payload.name)

    try:
        session.add(organization)
        await session.flush()

        membership = Membership(
            user_id=current_user.id,
            organization_id=organization.id,
            role="owner",
        )
        session.add(membership)

        await session.commit()

    except SQLAlchemyError:
        await session.rollback()
        raise

    await session.refresh(organization)
    return organization


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(
    session: SessionDep,
    current_user: CurrentUserDep,
):
    stmt = (
        select(Organization)
        .join(Membership, Organization.id == Membership.organization_id)
        .where(Membership.user_id == current_user.id)
        .order_by(Organization.created_at.desc(), Organization.id.desc())
    )
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post(
    "/{organization_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    organization_id: UUID,
    payload: MembershipCreate,
    session: SessionDep,
    owner_membership: OwnerDep,
):
    target_user = await session.get(User, payload.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    membership_lookup = await session.execute(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == payload.user_id,
        )
    )
    existing_membership = membership_lookup.scalar_one_or_none()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    membership = Membership(
        user_id=target_user.id,
        organization_id=owner_membership.organization_id,
        role=payload.role,
    )

    session.add(membership)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        driver_error = exc.orig.__cause__
        sqlstate = getattr(exc.orig, "sqlstate", None)
        constraint = getattr(driver_error, "constraint_name", None)

        if sqlstate == "23505" and constraint == "uq_memberships_user_organization":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            ) from None

        raise

    await session.refresh(membership)
    return membership


@router.get("/{organization_id}/members", response_model=list[MembershipRead])
async def get_organization_members(
    session: SessionDep,
    owner_membership: OwnerDep,
):
    query_stmt = select(Membership).where(
        Membership.organization_id == owner_membership.organization_id
    )

    query_res = await session.execute(query_stmt)
    return query_res.scalars().all()
