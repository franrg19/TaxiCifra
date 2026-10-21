import logging
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate, TicketFilters, TicketUpdate
from app.services import image_storage
from app.services.ocr.base import ExtractedTicket, OcrProvider
from app.services.vehicle_service import get_vehicle_or_404

logger = logging.getLogger(__name__)

# Campos obligatorios para confirmar un ticket, con su nombre para los mensajes de error
REQUIRED_TO_CONFIRM = {
    "date": "fecha",
    "vendor": "establecimiento",
    "category": "categoría",
    "net_amount": "base imponible",
    "vat": "IVA",
    "total": "total",
}

# Diferencia máxima admitida entre base imponible + IVA y el total (redondeos del ticket)
AMOUNT_TOLERANCE = Decimal("0.02")


def get_ticket_or_404(db: Session, ticket_id: int, user_id: int) -> Ticket:
    """Devuelve el ticket si existe y es del usuario; si no, responde 404."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.user_id != user_id:
        raise ApiError(status_code=404, detail="Ticket no encontrado", code="ticket_not_found")
    return ticket


def create_ticket(db: Session, user_id: int, data: TicketCreate) -> Ticket:
    """Crea un ticket a mano. Siempre nace pendiente de revisión."""
    if data.vehicle_id is not None:
        get_vehicle_or_404(db, data.vehicle_id, user_id)

    ticket = Ticket(user_id=user_id, status=TicketStatus.PENDING_REVIEW, **data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def create_ticket_from_image(db: Session, user_id: int, image: bytes, ocr: OcrProvider) -> Ticket:
    """Crea un ticket a partir de su foto: guarda la imagen y rellena los datos con el OCR.

    El ticket nace pendiente de revisión: lo leído por el OCR nunca es definitivo.
    """
    mime_type = image_storage.detect_mime_type(image)
    if mime_type is None:
        raise ApiError(
            status_code=415, detail="La imagen debe ser JPG o PNG", code="unsupported_image_type"
        )
    if len(image) > image_storage.MAX_IMAGE_SIZE:
        raise ApiError(
            status_code=413, detail="La imagen no puede superar 5 MB", code="image_too_large"
        )

    # Primero se guarda la imagen: así se conserva aunque el OCR falle
    image_path = image_storage.save_image(image, mime_type)
    extracted = _extract_safely(ocr, image, mime_type)

    ticket = Ticket(
        user_id=user_id,
        status=TicketStatus.PENDING_REVIEW,
        image_path=image_path,
        **_valid_fields(extracted),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _extract_safely(ocr: OcrProvider, image: bytes, mime_type: str) -> ExtractedTicket:
    """Lee el ticket con el OCR. Si el proveedor falla, devuelve un ticket vacío.

    Se captura cualquier error (red, tiempo de espera, respuesta ilegible...) porque un
    fallo del OCR NUNCA debe impedir al usuario guardar su ticket.
    """
    try:
        return ocr.extract(image, mime_type)
    except Exception:
        logger.warning("Fallo del proveedor OCR; el ticket se crea vacío", exc_info=True)
        return ExtractedTicket()


def _valid_fields(extracted: ExtractedTicket) -> dict[str, Any]:
    """Devuelve los datos leídos por el OCR, vaciando los que no cumplen las reglas del ticket.

    Se validan con las mismas reglas que el alta manual (TicketCreate): categoría existente,
    importes no negativos con dos decimales como máximo, establecimiento de 1 a 100 caracteres.
    """
    data = extracted.model_dump()
    try:
        return TicketCreate(**data).model_dump()
    except ValidationError as error:
        for invalid in error.errors():
            data[invalid["loc"][0]] = None
        return TicketCreate(**data).model_dump()


def get_ticket_image(db: Session, user_id: int, ticket_id: int) -> Path:
    """Devuelve la ruta en disco de la foto de un ticket del usuario, o responde 404."""
    ticket = get_ticket_or_404(db, ticket_id, user_id)
    path = image_storage.image_location(ticket.image_path) if ticket.image_path else None
    if path is None or not path.is_file():
        raise ApiError(status_code=404, detail="El ticket no tiene imagen", code="image_not_found")
    return path


def list_tickets(db: Session, user_id: int, filters: TicketFilters) -> tuple[Sequence[Ticket], int]:
    """Devuelve una página de tickets del usuario y el total que cumple los filtros."""
    conditions = [Ticket.user_id == user_id]
    if filters.date_from is not None:
        conditions.append(Ticket.date >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(Ticket.date <= filters.date_to)
    if filters.category is not None:
        conditions.append(Ticket.category == filters.category)
    if filters.status is not None:
        conditions.append(Ticket.status == filters.status)
    if filters.vehicle_id is not None:
        conditions.append(Ticket.vehicle_id == filters.vehicle_id)

    total = db.scalar(select(func.count()).select_from(Ticket).where(*conditions)) or 0
    query = (
        select(Ticket)
        .where(*conditions)
        .order_by(Ticket.date.desc().nulls_last(), Ticket.id.desc())
        .limit(filters.size)
        .offset((filters.page - 1) * filters.size)
    )
    return db.scalars(query).all(), total


def update_ticket(db: Session, user_id: int, ticket_id: int, data: TicketUpdate) -> Ticket:
    """Reemplaza los datos de un ticket del usuario.

    Tras editarlo, el ticket queda pendiente de revisión aunque estuviera confirmado: así
    todo gasto confirmado ha pasado siempre las validaciones de la confirmación.
    """
    ticket = get_ticket_or_404(db, ticket_id, user_id)
    if data.vehicle_id is not None:
        get_vehicle_or_404(db, data.vehicle_id, user_id)

    for field, value in data.model_dump().items():
        setattr(ticket, field, value)
    ticket.status = TicketStatus.PENDING_REVIEW
    db.commit()
    db.refresh(ticket)
    return ticket


def confirm_ticket(db: Session, user_id: int, ticket_id: int) -> Ticket:
    """Confirma un ticket del usuario si está completo y sus importes cuadran.

    Confirmar un ticket ya confirmado no es un error: se vuelve a validar y se devuelve igual.
    """
    ticket = get_ticket_or_404(db, ticket_id, user_id)
    _ensure_complete(ticket)
    _ensure_amounts_match(ticket)

    ticket.status = TicketStatus.CONFIRMED
    db.commit()
    db.refresh(ticket)
    return ticket


def _ensure_complete(ticket: Ticket) -> None:
    """Lanza 422 si falta algún campo obligatorio para confirmar."""
    missing = [
        label for field, label in REQUIRED_TO_CONFIRM.items() if getattr(ticket, field) is None
    ]
    if missing:
        raise ApiError(
            status_code=422,
            detail=f"Faltan campos para confirmar el ticket: {', '.join(missing)}",
            code="ticket_incomplete",
        )


def _ensure_amounts_match(ticket: Ticket) -> None:
    """Lanza 422 si base imponible + IVA no coincide con el total (con la tolerancia)."""
    expected = ticket.net_amount + ticket.vat
    if abs(expected - ticket.total) > AMOUNT_TOLERANCE:
        raise ApiError(
            status_code=422,
            detail=(
                f"Los importes no cuadran: base imponible + IVA suman {_euros(expected)} "
                f"y el total es {_euros(ticket.total)}"
            ),
            code="amounts_mismatch",
        )


def _euros(amount: Decimal) -> str:
    """Formatea un importe al estilo español: 50,00 €."""
    return f"{amount:.2f} €".replace(".", ",")


def delete_ticket(db: Session, user_id: int, ticket_id: int) -> None:
    """Elimina un ticket del usuario y, si tiene, su foto."""
    ticket = get_ticket_or_404(db, ticket_id, user_id)
    image_path = ticket.image_path
    db.delete(ticket)
    db.commit()
    # La foto se borra después del commit: si fallara la base de datos, el ticket seguiría con ella
    if image_path:
        image_storage.delete_image(image_path)
