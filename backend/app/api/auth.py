from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.deps import get_current_user
from app.core.config import settings
from app.api.schemas import (
    UserCreate, UserOut, LoginRequest, TokenResponse,
    RefreshRequest, UpdateProfileRequest, UpdatePasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_OPTS = dict(
    httponly=True,
    samesite="lax",
    secure=False,  # set True in production with HTTPS
)


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user: Optional[User] = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(key="access_token", value=access_token,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **_COOKIE_OPTS)
    response.set_cookie(key="refresh_token", value=refresh_token,
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **_COOKIE_OPTS)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: Optional[str] = Cookie(default=None, alias="refresh_token"),
    body: Optional[RefreshRequest] = None,
):
    token = refresh_token_cookie or (body.refresh_token if body else None)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user: Optional[User] = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access = create_access_token(user.id, user.email)
    new_refresh = create_refresh_token(user.id)

    response.set_cookie(key="access_token", value=new_access,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **_COOKIE_OPTS)
    response.set_cookie(key="refresh_token", value=new_refresh,
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **_COOKIE_OPTS)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── Update Profile ────────────────────────────────────────────────────────────

@router.put("/profile", response_model=UserOut)
async def update_profile(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.full_name = body.full_name
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return current_user


# ── Update Password ───────────────────────────────────────────────────────────

@router.put("/password")
async def update_password(
    body: UpdatePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(body.new_password)
    db.add(current_user)
    await db.flush()
    return {"message": "Password updated successfully"}
