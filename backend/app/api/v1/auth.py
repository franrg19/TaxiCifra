from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.models import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession) -> User:
    """Registra un usuario nuevo."""
    return auth_service.register_user(db, data)


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: DbSession) -> Token:
    """Inicia sesión y devuelve un token JWT."""
    return auth_service.login(db, data)
