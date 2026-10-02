from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.errors import ApiError
from app.core.security import JWT_ALGORITHM, create_access_token
from app.models import User


@pytest.fixture
def user(db: Session) -> User:
    """Usuario guardado en la base de datos de test."""
    user = User(name="Ana", email="ana@example.com", password_hash="hash")
    db.add(user)
    db.flush()
    return user


def bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def assert_not_authenticated(credentials: HTTPAuthorizationCredentials | None, db: Session) -> None:
    with pytest.raises(ApiError) as error:
        get_current_user(credentials, db)
    assert error.value.status_code == 401
    assert error.value.code == "not_authenticated"


def test_valid_token_returns_its_user(db: Session, user: User) -> None:
    token = create_access_token(user.id)

    assert get_current_user(bearer(token), db) is user


def test_missing_token_is_rejected(db: Session) -> None:
    assert_not_authenticated(None, db)


def test_malformed_token_is_rejected(db: Session) -> None:
    assert_not_authenticated(bearer("esto-no-es-un-token"), db)


def test_expired_token_is_rejected(db: Session, user: User) -> None:
    payload = {"sub": str(user.id), "exp": datetime.now(UTC) - timedelta(minutes=1)}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)

    assert_not_authenticated(bearer(token), db)


def test_token_signed_with_another_secret_is_rejected(db: Session, user: User) -> None:
    payload = {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(hours=1)}
    token = jwt.encode(payload, "otra-clave-distinta-de-la-real-0123456789", algorithm="HS256")

    assert_not_authenticated(bearer(token), db)


def test_token_of_deleted_user_is_rejected(db: Session) -> None:
    token = create_access_token(999_999)

    assert_not_authenticated(bearer(token), db)
