import datetime as dt
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel


class ExtractedTicket(BaseModel):
    """Datos que el proveedor OCR/IA ha leído de un ticket. Lo que no consigue leer queda vacío."""

    date: dt.date | None = None
    vendor: str | None = None
    net_amount: Decimal | None = None
    vat: Decimal | None = None
    total: Decimal | None = None
    category: str | None = None


class OcrProvider(Protocol):
    """Lo que debe saber hacer cualquier proveedor OCR/IA: leer una imagen de un ticket."""

    def extract(self, image: bytes, mime_type: str) -> ExtractedTicket: ...
