import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import TicketCategory


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


class CategoryExpense(BaseModel):
    """Gasto confirmado de una categoría en el periodo."""

    category: TicketCategory
    total: Decimal


class MonthlyFilters(BaseModel):
    """Año y vehículo de la evolución mensual. Sin año se usa el actual."""

    year: int = Field(default_factory=lambda: dt.date.today().year, ge=2000, le=2100)
    vehicle_id: int | None = None


class MonthlyTotals(BaseModel):
    """Gastos, ingresos y beneficio de un mes (1 = enero)."""

    month: int
    expenses: Decimal
    incomes: Decimal
    profit: Decimal
