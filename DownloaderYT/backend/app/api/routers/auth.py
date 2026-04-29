from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user, require_admin
from app.core.config import get_settings
from app.core.security import build_session_expiry, generate_session_token, hash_password, hash_session_token, verify_password
from app.db.models import Setting, User
from app.db.session_store import create_session, revoke_session_by_hash
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, MeResponse, RegisterRequest, RegisterResponse
from app.schemas.user import UserPublic


router = APIRouter()


def _set_auth_cookie(response: Response, *, token: str, max_age_seconds: int) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=max_age_seconds,
        expires=max_age_seconds,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.session_cookie_name, path="/")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(db_session)) -> LoginResponse:
    settings = get_settings()
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session_token = generate_session_token()
    token_hash = hash_session_token(session_token, settings.secret_key)
    expires_at = build_session_expiry(settings.session_ttl_hours)
    create_session(db, user_id=user.id, token_hash=token_hash, expires_at=expires_at)

    _set_auth_cookie(response, token=session_token, max_age_seconds=settings.session_ttl_hours * 3600)

    return LoginResponse(
        message="login ok",
        user=UserPublic(
            id=user.id,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
        ),
        expires_at=expires_at,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> LogoutResponse:
    settings = get_settings()
    session_token = request.cookies.get(settings.session_cookie_name)
    _clear_auth_cookie(response)
    if session_token:
        token_hash = hash_session_token(session_token, settings.secret_key)
        revoke_session_by_hash(db, token_hash=token_hash)
    return LogoutResponse(message=f"logout ok ({current_user.username})")


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user=UserPublic(
            id=current_user.id,
            username=current_user.username,
            role=current_user.role,
            created_at=current_user.created_at,
        )
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
) -> RegisterResponse:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username cannot be empty")
    if username.lower() == "admin":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is reserved")

    existing_user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.flush()
    db.add(Setting(user_id=user.id))
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        message="user created",
        user=UserPublic(
            id=user.id,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
        ),
    )
