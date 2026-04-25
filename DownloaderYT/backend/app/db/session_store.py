from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Session as UserSession
from app.db.models import User


def create_session(
    db: Session,
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> UserSession:
    db_session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked_at=None,
        last_seen_at=datetime.utcnow(),
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_active_session_and_user(
    db: Session,
    *,
    token_hash: str,
) -> tuple[UserSession, User] | None:
    now = datetime.utcnow()
    query = (
        select(UserSession, User)
        .join(User, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )
    row = db.execute(query).first()
    if row is None:
        return None
    return row[0], row[1]


def revoke_session_by_hash(db: Session, *, token_hash: str) -> bool:
    query = select(UserSession).where(
        UserSession.token_hash == token_hash,
        UserSession.revoked_at.is_(None),
    )
    db_session = db.execute(query).scalar_one_or_none()
    if db_session is None:
        return False

    db_session.revoked_at = datetime.utcnow()
    db.commit()
    return True


def touch_session(db: Session, *, db_session: UserSession) -> None:
    db_session.last_seen_at = datetime.utcnow()
    db.commit()

