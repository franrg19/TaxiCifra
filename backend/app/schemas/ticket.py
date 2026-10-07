import datetime as dt
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models import TicketCategory, TicketStatus

# Importe en euros: no negativo y con dos decimales como máximo
Amount = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class TicketCreate(BaseModel):
    """Datos de entrada para crear un ticket a mano. Todo es opcional: nace como borrador."""

    date: dt.date | None = None
    vendor: str | None = Field(default=None, min_length=1, max_length=100)
    category: TicketCategory | None = None
    net_amount: Amount | None = None
    vat: Amount | None = None
    total: Amount | None = None
    vehicle_id: int | None = None


class TicketFilters(BaseModel):
    """Parámetros de consulta del listado de tickets: paginación y filtros opcionales."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    category: TicketCategory | None = None
    status: TicketStatus | None = None
    vehicle_id: int | None = None


class TicketRead(BaseModel):
    """Datos del ticket que devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int | None
    date: dt.date | None
    vendor: str | None
    category: TicketCategory | None
    net_amount: Decimal | None
    vat: Decimal | None
    total: Decimal | None
    status: TicketStatus
    created_at: dt.datetime
