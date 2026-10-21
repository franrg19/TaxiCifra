from sqlalchemy.orm import Session

from app.models import Income
from app.schemas.income import IncomeCreate
from app.services.vehicle_service import get_vehicle_or_404


def create_income(db: Session, user_id: int, data: IncomeCreate) -> Income:
    """Registra un ingreso del usuario."""
    if data.vehicle_id is not None:
        get_vehicle_or_404(db, data.vehicle_id, user_id)

    income = Income(user_id=user_id, **data.model_dump())
    db.add(income)
    db.commit()
    db.refresh(income)
    return income
