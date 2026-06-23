import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


async def _resolve_user(
    access_token: str | None,
    db: AsyncSession,
) -> User | None:
    if not access_token:
        return None
    try:
        payload = decode_token(access_token)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            return None
    except jwt.PyJWTError:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id_str)))
    return result.scalar_one_or_none()


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _resolve_user(access_token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登入或 session 已過期",
        )
    return user


async def get_optional_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    return await _resolve_user(access_token, db)
