import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, get_session


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="Expense & Approval API",
    lifespan=lifespan,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness(session: SessionDep):
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError):
        logger.warning("Database readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from None

    return {"status": "ready"}