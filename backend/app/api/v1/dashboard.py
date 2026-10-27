from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardFilters, DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    filters: Annotated[DashboardFilters, Query()], user: CurrentUser, db: DbSession
) -> DashboardSummary:
    """Resumen económico del usuario autenticado en un periodo y, opcionalmente, un vehículo."""
    return dashboard_service.get_summary(db, user.id, filters)
