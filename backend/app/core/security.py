from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

JWT_ALGORITHM = "HS256"

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Devuelve el hash argon2 de la contraseña (incluye la sal)."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Indica si la contraseña corresponde al hash guardado."""
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: int) -> str:
    """Crea un token JWT firmado que identifica al usuario y caduca a las 24 horas."""
    expires_at = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
