import datetime as dt
import json
from collections.abc import Generator
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.api.deps import get_ocr_provider
from app.core.config import settings
from app.services.ocr.base import ExtractedTicket, OcrProvider
from app.services.ocr.claude import ClaudeOcrProvider
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


# --- Proveedor real (Claude), con un cliente falso: nunca se llama a la API ---

READ_TICKET = {
    "date": "2026-10-05",
    "vendor": "Petroprix",
    "net_amount": "41.32",
    "vat": "8.68",
    "total": "50.00",
    "category": "combustible",
}


class FakeMessages:
    """Imita client.messages: guarda la petición y devuelve una respuesta preparada."""

    def __init__(self, text: str, stop_reason: str) -> None:
        self.request: dict = {}
        self._response = SimpleNamespace(
            stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)]
        )

    def create(self, **request: object) -> SimpleNamespace:
        self.request = request
        return self._response


def claude_with_response(
    data: dict, stop_reason: str = "end_turn"
) -> tuple[ClaudeOcrProvider, FakeMessages]:
    """Proveedor Claude cuyo cliente responde con los datos indicados."""
    messages = FakeMessages(json.dumps(data), stop_reason)
    client = SimpleNamespace(messages=messages)
    return ClaudeOcrProvider(client, "claude-haiku-5-5"), messages


def test_claude_provider_returns_read_ticket() -> None:
    provider, _ = claude_with_response(READ_TICKET)

    extracted = provider.extract(b"foto", "image/jpeg")

    assert extracted == ExtractedTicket(
        date=dt.date(2026, 10, 5),
        vendor="Petroprix",
        net_amount=Decimal("41.32"),
        vat=Decimal("8.68"),
        total=Decimal("50.00"),
        category="combustible",
    )


def test_claude_provider_sends_image_model_and_schema() -> None:
    provider, messages = claude_with_response(READ_TICKET)

    provider.extract(b"foto", "image/png")

    request = messages.request
    assert request["model"] == "claude-haiku-5-5"
    image = request["messages"][0]["content"][0]
    assert image["source"] == {"type": "base64", "media_type": "image/png", "data": "Zm90bw=="}
    assert request["output_config"]["format"]["type"] == "json_schema"


def test_claude_provider_drops_unreadable_fields_and_keeps_the_rest() -> None:
    provider, _ = claude_with_response({**READ_TICKET, "date": "2026-02-31", "vat": "ocho"})

    extracted = provider.extract(b"foto", "image/jpeg")

    assert extracted.date is None
    assert extracted.vat is None
    assert extracted.total == Decimal("50.00")
    assert extracted.vendor == "Petroprix"


def test_claude_provider_fails_on_incomplete_response() -> None:
    provider, _ = claude_with_response(READ_TICKET, stop_reason="max_tokens")

    with pytest.raises(RuntimeError):
        provider.extract(b"foto", "image/jpeg")


# --- Elección del proveedor ---


@pytest.fixture
def fresh_provider() -> Generator[None, None, None]:
    """Vacía la caché de get_ocr_provider antes y después del test."""
    get_ocr_provider.cache_clear()
    yield
    get_ocr_provider.cache_clear()


@pytest.mark.usefixtures("fresh_provider")
def test_without_api_key_the_simulated_provider_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "anthropic_api_key", None)

    assert isinstance(get_ocr_provider(), FakeOcrProvider)


@pytest.mark.usefixtures("fresh_provider")
def test_with_api_key_claude_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "anthropic_api_key", "clave-de-prueba")

    assert isinstance(get_ocr_provider(), ClaudeOcrProvider)
