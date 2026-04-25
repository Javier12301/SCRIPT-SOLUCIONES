from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.api.dependencies import require_admin
from app.db.models import User


def test_require_admin_raises_403_for_regular_user() -> None:
    regular_user = User(username="u", password_hash="h", role="user")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(regular_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Admin role required"


def test_require_admin_returns_user_for_admin_role() -> None:
    admin_user = User(username="admin", password_hash="h", role="admin")
    assert require_admin(admin_user) is admin_user
