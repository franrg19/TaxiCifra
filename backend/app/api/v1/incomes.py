from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.models import Income
from app.schemas.income import IncomeCreate, IncomeRead
from app.services import income_service

router = APIRouter(prefix="/incomes", tags=["incomes"])


@router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
def create_income(data: IncomeCreate, user: CurrentUser, db: DbSession) -> Income:
    """Registra un ingreso del usuario autenticado."""
    return income_service.create_income(db, user.id, data)
