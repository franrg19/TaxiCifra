import logging
from collections.abc import Generator
from functools import cache
from typing import Annotated

import anthropic
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.db.database import SessionLocal
from app.models import User
from app.services.ocr.base import OcrProvider
from app.services.ocr.claude import ClaudeOcrProvider
from app.services.ocr.fake import FakeOcrProvider

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Abre una sesión de base de datos por petición y la cierra al terminar."""
    with SessionLocal() as db:
        yield db


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Devuelve el usuario del token JWT de la cabecera Authorization, o responde 401."""
    user_id = decode_access_token(credentials.credentials) if credentials else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise ApiError(status_code=401, detail="No autenticado", code="not_authenticated")
    return user


@cache
def get_ocr_provider() -> OcrProvider:
    """Devuelve el proveedor OCR/IA: Claude si hay clave de Anthropic; si no, el simulado.

    Se crea una sola vez (@cache) y se reutiliza en todas las peticiones.
    """
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY no configurada: se usa el proveedor OCR simulado")
        return FakeOcrProvider()
    # Si el proveedor tarda o falla, la subida no se bloquea: el ticket se crea vacío
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=30.0, max_retries=1)
    return ClaudeOcrProvider(client, settings.ocr_model)


# Alias para declarar las dependencias en las rutas sin repetir Annotated
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OcrService = Annotated[OcrProvider, Depends(get_ocr_provider)]
