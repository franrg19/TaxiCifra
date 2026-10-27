import datetime as dt
from decimal import Decimal

from pydantic import BaseModel


class DashboardFilters(BaseModel):
    """Periodo y vehículo del dashboard. Sin fechas se usa todo el histórico."""

    date_from: dt.date | None = None
    date_to: dt.date | None = None
    vehicle_id: int | None = None


class DashboardSummary(BaseModel):
    """Resumen económico del periodo."""

    expenses: Decimal
    incomes: Decimal
    profit: Decimal
    ticket_count: int
    # None = "sin datos": no hay ningún vehículo con al menos dos lecturas en el periodo
    km_driven: int | None
    cost_per_km: Decimal | None
