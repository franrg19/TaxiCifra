import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class IncomeCreate(BaseModel):
    """Datos de entrada para registrar un ingreso. Fecha e importe son obligatorios."""

    date: dt.date
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, min_length=1, max_length=255)
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
