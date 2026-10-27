import base64
import json
from typing import Any

import anthropic
from pydantic import ValidationError

from app.models import TicketCategory
from app.services.ocr.base import ExtractedTicket

PROMPT = """Eres el lector de tickets de una aplicación para taxistas autónomos en España.
Extrae de la foto del ticket estos datos:

- date: fecha del ticket en formato AAAA-MM-DD.
- vendor: nombre del establecimiento o empresa que emite el ticket, tal como aparece.
- net_amount: base imponible (importe sin IVA). Si hay varios tipos de IVA, la suma de las bases.
- vat: cuota de IVA en euros (no el porcentaje). Si hay varios tipos, la suma de las cuotas.
- total: importe total pagado.
- category: la categoría del gasto para un taxista, una de estas:
    combustible (gasolina, diésel, GLP, carga eléctrica), mantenimiento (revisiones, aceite,
    neumáticos, ITV), seguro, limpieza (lavado del coche), reparaciones (averías, chapa, taller),
    emisora (cuota de la emisora o radio-taxi), autonomo (cuota de autónomos, gestoría),
    datafono (cuota o comisiones del datáfono), otros (cualquier otra cosa).

Reglas:
- Los importes, con punto decimal y dos decimales: "41.32".
- Si un dato no aparece o no se lee con seguridad, devuelve null. No inventes datos.
- Si el ticket muestra el total y el IVA pero no la base, la base es total - IVA.
- Si solo muestra el total y un único tipo de IVA incluido (p. ej. "IVA incluido 21%"),
  calcula la base (total / 1,21, redondeada a céntimos) y el IVA (total - base)."""

_NULLABLE_STRING = {"anyOf": [{"type": "string"}, {"type": "null"}]}

# Esquema de la respuesta: la API garantiza que el JSON devuelto lo cumple
SCHEMA = {
    "type": "object",
    "properties": {
        "date": _NULLABLE_STRING,
        "vendor": _NULLABLE_STRING,
        "net_amount": _NULLABLE_STRING,
        "vat": _NULLABLE_STRING,
        "total": _NULLABLE_STRING,
        "category": {
            "anyOf": [
                {"type": "string", "enum": [category.value for category in TicketCategory]},
                {"type": "null"},
            ]
        },
    },
    "required": ["date", "vendor", "net_amount", "vat", "total", "category"],
    "additionalProperties": False,
}


class ClaudeOcrProvider:
    """Lee tickets con un modelo de IA con visión de Anthropic (Claude).

    Elegido tras evaluar Haiku, Sonnet y Opus con fotos reales: los tres acertaron todos
    los campos y Haiku era el más barato. El modelo se configura con OCR_MODEL.
    """

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def extract(self, image: bytes, mime_type: str) -> ExtractedTicket:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=16000,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64.standard_b64encode(image).decode("utf-8"),
                            },
                        },
                        {"type": "text", "text": PROMPT},
                    ],
                }
            ],
        )
        # Una respuesta cortada o rechazada no se interpreta: el servicio de tickets
        # captura el error y crea el ticket vacío para que el usuario lo rellene
        if response.stop_reason != "end_turn":
            raise RuntimeError(f"Respuesta del OCR incompleta (stop_reason={response.stop_reason})")
        text = next(block.text for block in response.content if block.type == "text")
        return _to_extracted_ticket(json.loads(text))


def _to_extracted_ticket(data: dict[str, Any]) -> ExtractedTicket:
    """Convierte la respuesta en ExtractedTicket, vaciando los campos que no se puedan leer.

    Por ejemplo, una fecha imposible no debe hacer perder el resto de datos leídos.
    """
    try:
        return ExtractedTicket.model_validate(data)
    except ValidationError as error:
        for invalid in error.errors():
            data[invalid["loc"][0]] = None
        return ExtractedTicket.model_validate(data)
