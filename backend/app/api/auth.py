from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AccountUpdateRequest, LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE = "access_token"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

# CSRF 防護策略：
# - Cookie 設定 SameSite=Lax，瀏覽器不會在跨站的狀態變更請求（POST/PUT/DELETE）
#   附上此 cookie，僅在同站請求或頂層導覽的安全方法（GET）才會附上。
# - CORS 中介層僅允許 settings.cors_origins 明確列出的來源，且要求
#   Content-Type: application/json，跨站請求會先觸發預檢（preflight），
#   在未列入白名單時被瀏覽器擋下，無法完成實際的狀態變更請求。
# 兩者疊加已足以防禦傳統 CSRF；本專案不使用第三方需要另外導入 CSRF token
# 機制的框架，故未額外實作 CSRF token。


def _set_auth_cookie(response: Response, user: User) -> None:
    token = create_access_token({"sub": str(user.id), "tv": user.token_version})
    response.set_cookie(
        key=_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=_COOKIE_MAX_AGE,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤")

    _set_auth_cookie(response, user)
    return {"user": user}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    _: User = Depends(get_current_user),
):
    response.delete_cookie(
        _COOKIE,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: AccountUpdateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="目前密碼不正確")

    if body.username:
        current_user.username = body.username
    if body.email:
        current_user.email = body.email

    password_changed = bool(body.new_password)
    if password_changed:
        current_user.hashed_password = hash_password(body.new_password)
        # 讓所有裝置上舊的 token 立即失效，只有這次請求換發的新 token 有效
        current_user.token_version += 1

    await db.commit()
    await db.refresh(current_user)

    if password_changed:
        _set_auth_cookie(response, current_user)

    return current_user
