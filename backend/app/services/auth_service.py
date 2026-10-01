from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate


def register_user(db: Session, data: UserCreate) -> User:
    """Crea un usuario nuevo. El email se guarda en minúsculas y debe ser único."""
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise ApiError(
            status_code=409,
            detail="Ya existe una cuenta con ese email",
            code="email_already_registered",
        )

    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
