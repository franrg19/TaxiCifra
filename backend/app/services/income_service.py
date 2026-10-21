from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Income
from app.schemas.income import IncomeCreate, IncomeFilters, IncomeUpdate
from app.services.vehicle_service import get_vehicle_or_404


def get_income_or_404(db: Session, income_id: int, user_id: int) -> Income:
    """Devuelve el ingreso si existe y es del usuario; si no, responde 404."""
    income = db.get(Income, income_id)
    if income is None or income.user_id != user_id:
        raise ApiError(status_code=404, detail="Ingreso no encontrado", code="income_not_found")
    return income


def create_income(db: Session, user_id: int, data: IncomeCreate) -> Income:
    """Registra un ingreso del usuario."""
    if data.vehicle_id is not None:
        get_vehicle_or_404(db, data.vehicle_id, user_id)

    income = Income(user_id=user_id, **data.model_dump())
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def list_incomes(db: Session, user_id: int, filters: IncomeFilters) -> tuple[Sequence[Income], int]:
    """Devuelve una página de ingresos del usuario y el total que cumple los filtros."""
    conditions = [Income.user_id == user_id]
    if filters.date_from is not None:
        conditions.append(Income.date >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(Income.date <= filters.date_to)
    if filters.vehicle_id is not None:
        conditions.append(Income.vehicle_id == filters.vehicle_id)

    total = db.scalar(select(func.count()).select_from(Income).where(*conditions)) or 0
    query = (
        select(Income)
        .where(*conditions)
        .order_by(Income.date.desc(), Income.id.desc())
        .limit(filters.size)
        .offset((filters.page - 1) * filters.size)
    )
    return db.scalars(query).all(), total


def update_income(db: Session, user_id: int, income_id: int, data: IncomeUpdate) -> Income:
    """Reemplaza los datos de un ingreso del usuario."""
    income = get_income_or_404(db, income_id, user_id)
    if data.vehicle_id is not None:
        get_vehicle_or_404(db, data.vehicle_id, user_id)

    for field, value in data.model_dump().items():
        setattr(income, field, value)
    db.commit()
    db.refresh(income)
    return income


def delete_income(db: Session, user_id: int, income_id: int) -> None:
    """Elimina un ingreso del usuario."""
    income = get_income_or_404(db, income_id, user_id)
    db.delete(income)
    db.commit()
