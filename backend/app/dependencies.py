from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User
from app.security import decode_access_token

from uuid import UUID

from sqlalchemy import select

from app.models.membership import Membership

bearer = HTTPBearer(auto_error=False)

CredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer),
]

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: CredentialsDep,
    session: SessionDep,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise unauthorized from None

    user = await session.get(User, user_id)

    if user is None:
        raise unauthorized

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_organization_membership(
    organization_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> Membership:

    mebership_query = await session.execute(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == current_user.id,
        )
    )
    res = mebership_query.scalar_one_or_none()

    if res is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    return res


MembershipDep = Annotated[
    Membership,
    Depends(get_organization_membership),
]


async def require_organization_owner(
    membership: MembershipDep,
) -> Membership:

    if membership.role != "owner":
        raise HTTPException(
            status_code=403, detail="Organization owner access required"
        )
    return membership
