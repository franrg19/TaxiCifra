from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

REGISTER_URL = "/api/v1/auth/register"
VALID_USER = {"name": "Ana", "email": "ana@example.com", "password": "secreto123"}


def test_register_returns_created_user_without_password(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json=VALID_USER)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ana"
    assert body["email"] == "ana@example.com"
    assert "id" in body
    assert "created_at" in body
    assert "password" not in body
    assert "password_hash" not in body


def test_register_stores_password_hashed(client: TestClient, db: Session) -> None:
    client.post(REGISTER_URL, json=VALID_USER)

    user = db.scalar(select(User).where(User.email == "ana@example.com"))
    assert user is not None
    assert user.password_hash != VALID_USER["password"]
    assert user.password_hash.startswith("$argon2")


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    client.post(REGISTER_URL, json=VALID_USER)

    response = client.post(REGISTER_URL, json={**VALID_USER, "email": "ANA@example.com"})

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Ya existe una cuenta con ese email",
        "code": "email_already_registered",
    }


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json={**VALID_USER, "email": "no-es-un-email"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Datos no válidos en: email", "code": "validation_error"}


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json={**VALID_USER, "password": "corta"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
