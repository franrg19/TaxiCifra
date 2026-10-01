from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Abre una sesión de base de datos por petición y la cierra al terminar."""
    with SessionLocal() as db:
        yield db
