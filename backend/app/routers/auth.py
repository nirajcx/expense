from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.db import get_session
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import hash_password


from app.models.user import User
from app.dependencies import get_current_user


from app.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def signup(payload: UserCreate, session: SessionDep):

    email = str(payload.email).lower()

    result = await session.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    password_hash = await run_in_threadpool(
        hash_password,
        payload.password,
    )

    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=password_hash,
    )

    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        driver_error = exc.orig.__cause__
        sqlstate = getattr(exc.orig, "sqlstate", None)
        constraint = getattr(driver_error, "constraint_name", None)

        if sqlstate == "23505" and constraint == "users_email_key":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            ) from None

        raise

    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep):
    email = str(payload.email).lower()

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    password_valid = await run_in_threadpool(
        verify_password, payload.password, user.password_hash
    )
    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        token_type="bearer",
        expires_in=get_settings().access_token_minutes * 60,
    )

    # Valid credentials par token response


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUserDep):
    return current_user
