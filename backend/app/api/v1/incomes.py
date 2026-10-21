from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models import Income
from app.schemas.income import IncomeCreate, IncomeFilters, IncomeRead, IncomeUpdate
from app.schemas.pagination import Page
from app.services import income_service

router = APIRouter(prefix="/incomes", tags=["incomes"])


@router.get("", response_model=Page[IncomeRead])
def list_incomes(
    filters: Annotated[IncomeFilters, Query()], user: CurrentUser, db: DbSession
) -> Page[IncomeRead]:
    """Lista los ingresos del usuario autenticado, con filtros y paginación."""
    items, total = income_service.list_incomes(db, user.id, filters)
    return Page[IncomeRead](items=items, total=total, page=filters.page, size=filters.size)


@router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
def create_income(data: IncomeCreate, user: CurrentUser, db: DbSession) -> Income:
    """Registra un ingreso del usuario autenticado."""
    return income_service.create_income(db, user.id, data)


@router.put("/{income_id}", response_model=IncomeRead)
def update_income(income_id: int, data: IncomeUpdate, user: CurrentUser, db: DbSession) -> Income:
    """Edita un ingreso del usuario autenticado."""
    return income_service.update_income(db, user.id, income_id, data)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(income_id: int, user: CurrentUser, db: DbSession) -> None:
    """Elimina un ingreso del usuario autenticado."""
    income_service.delete_income(db, user.id, income_id)
