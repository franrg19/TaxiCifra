import datetime as dt
from decimal import Decimal

from app.services.ocr.base import ExtractedTicket


class FakeOcrProvider:
    """Proveedor simulado: devuelve siempre el mismo ticket, sin mirar la imagen.

    Sirve para desarrollar y probar el flujo de subida sin depender de un servicio externo.
    """

    def extract(self, image: bytes, mime_type: str) -> ExtractedTicket:
        return ExtractedTicket(
            date=dt.date(2026, 10, 5),
            vendor="Gasolinera Sol",
            net_amount=Decimal("41.32"),
            vat=Decimal("8.68"),
            total=Decimal("50.00"),
            category="combustible",
        )
