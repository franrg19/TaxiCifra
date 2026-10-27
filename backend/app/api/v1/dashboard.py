from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import (
    CategoryExpense,
    DashboardFilters,
    DashboardSummary,
    MonthlyFilters,
    MonthlyTotals,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    filters: Annotated[DashboardFilters, Query()], user: CurrentUser, db: DbSession
) -> DashboardSummary:
    """Resumen económico del usuario autenticado en un periodo y, opcionalmente, un vehículo."""
    return dashboard_service.get_summary(db, user.id, filters)


@router.get("/by-category", response_model=list[CategoryExpense])
def get_by_category(
    filters: Annotated[DashboardFilters, Query()], user: CurrentUser, db: DbSession
) -> list[CategoryExpense]:
    """Gasto confirmado por categoría del usuario autenticado, de mayor a menor."""
    return dashboard_service.get_by_category(db, user.id, filters)


@router.get("/monthly", response_model=list[MonthlyTotals])
def get_monthly(
    filters: Annotated[MonthlyFilters, Query()], user: CurrentUser, db: DbSession
) -> list[MonthlyTotals]:
    """Gastos, ingresos y beneficio de cada mes del año del usuario autenticado."""
    return dashboard_service.get_monthly(db, user.id, filters)
