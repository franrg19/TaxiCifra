import datetime as dt
from decimal import Decimal

from app.services.ocr.base import ExtractedTicket, OcrProvider
from app.services.ocr.fake import FakeOcrProvider


def test_extracted_ticket_is_empty_by_default() -> None:
    extracted = ExtractedTicket()

    assert extracted.model_dump() == {
        "date": None,
        "vendor": None,
        "net_amount": None,
        "vat": None,
        "total": None,
        "category": None,
    }


def test_extracted_ticket_converts_text_to_date_and_decimal() -> None:
    extracted = ExtractedTicket(date="2026-10-05", total="50.00")

    assert extracted.date == dt.date(2026, 10, 5)
    assert extracted.total == Decimal("50.00")


def test_fake_provider_returns_fixed_ticket() -> None:
    provider: OcrProvider = FakeOcrProvider()

    extracted = provider.extract(b"cualquier imagen", "image/jpeg")

    assert extracted == ExtractedTicket(
        date=dt.date(2026, 10, 5),
        vendor="Gasolinera Sol",
        net_amount=Decimal("41.32"),
        vat=Decimal("8.68"),
        total=Decimal("50.00"),
        category="combustible",
    )


def test_fake_provider_returns_amounts_that_can_be_confirmed() -> None:
    extracted = FakeOcrProvider().extract(b"", "image/png")

    assert extracted.net_amount + extracted.vat == extracted.total
