from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import JWT_ALGORITHM

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
USER = {"name": "Ana", "email": "ana@example.com", "password": "secreto123"}
INVALID_CREDENTIALS = {"detail": "Email o contraseña incorrectos", "code": "invalid_credentials"}


@pytest.fixture
def user_id(client: TestClient) -> int:
    """Registra un usuario y devuelve su id."""
    return client.post(REGISTER_URL, json=USER).json()["id"]


def test_login_returns_bearer_token(client: TestClient, user_id: int) -> None:
    response = client.post(LOGIN_URL, json={"email": USER["email"], "password": USER["password"]})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_token_identifies_user_and_expires_in_24_hours(
    client: TestClient, user_id: int
) -> None:
    response = client.post(LOGIN_URL, json={"email": USER["email"], "password": USER["password"]})

    payload = jwt.decode(
        response.json()["access_token"], settings.jwt_secret, algorithms=[JWT_ALGORITHM]
    )
    assert payload["sub"] == str(user_id)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected = datetime.now(UTC) + timedelta(hours=24)
    assert abs(expires_at - expected) < timedelta(minutes=1)


def test_login_ignores_email_case(client: TestClient, user_id: int) -> None:
    response = client.post(
        LOGIN_URL, json={"email": "ANA@example.com", "password": USER["password"]}
    )

    assert response.status_code == 200


def test_login_rejects_wrong_password(client: TestClient, user_id: int) -> None:
    response = client.post(LOGIN_URL, json={"email": USER["email"], "password": "incorrecta1"})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(LOGIN_URL, json={"email": "nadie@example.com", "password": "secreto123"})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS
