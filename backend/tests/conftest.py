from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_ocr_provider
from app.core.config import settings
from app.db.database import Base
from app.main import app
from app.services.ocr.fake import FakeOcrProvider


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Crea (si no existe) una base de datos solo para tests y sus tablas."""
    url = make_url(settings.database_url)
    test_url = url.set(database=f"{url.database}_test")

    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": test_url.database},
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    admin_engine.dispose()

    test_engine = create_engine(test_url)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Generator[Session, None, None]:
    """Sesión dentro de una transacción que se deshace al acabar cada test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP cuya API usa la sesión de test en lugar de la real."""
    app.dependency_overrides[get_db] = lambda: db
    # Los tests NUNCA llaman a un proveedor OCR real, aunque haya clave en el .env
    app.dependency_overrides[get_ocr_provider] = FakeOcrProvider
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, name: str, email: str) -> dict[str, str]:
    """Registra un usuario, inicia sesión y devuelve la cabecera Authorization."""
    credentials = {"email": email, "password": "secreto123"}
    client.post("/api/v1/auth/register", json={"name": name, **credentials})
    token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Cabecera de autenticación de un usuario registrado."""
    return _register_and_login(client, "Ana", "ana@example.com")


@pytest.fixture
def other_auth_headers(client: TestClient) -> dict[str, str]:
    """Cabecera de autenticación de un segundo usuario, para probar la autorización."""
    return _register_and_login(client, "Berto", "berto@example.com")
