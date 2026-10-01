from argon2 import PasswordHasher

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Devuelve el hash argon2 de la contraseña (incluye la sal)."""
    return _hasher.hash(password)
