from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Datos de entrada del inicio de sesión."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Token de acceso que devuelve el inicio de sesión."""

    access_token: str
    token_type: str = "bearer"
