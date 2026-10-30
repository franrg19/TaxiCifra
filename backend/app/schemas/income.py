import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination import PageParams


class IncomeCreate(BaseModel):
    """Datos de entrada para registrar un ingreso. Solo la descripción es opcional."""

    date: dt.date
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    vehicle_id: int
    description: str | None = Field(default=None, min_length=1, max_length=255)


class IncomeUpdate(IncomeCreate):
    """Datos de entrada para editar un ingreso. Se reemplazan todos los campos."""


class IncomeFilters(PageParams):
    """Parámetros de consulta del listado de ingresos: paginación y filtros opcionales."""

    date_from: dt.date | None = None
    date_to: dt.date | None = None
    vehicle_id: int | None = None


class IncomeRead(BaseModel):
    """Datos del ingreso que devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int | None
    date: dt.date
    amount: Decimal
    description: str | None
    created_at: dt.datetime
