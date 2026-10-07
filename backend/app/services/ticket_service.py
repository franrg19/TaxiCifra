from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate, TicketFilters, TicketUpdate
from app.services.vehicle_service import get_vehicle_or_404


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


def delete_ticket(db: Session, user_id: int, ticket_id: int) -> None:
    """Elimina un ticket del usuario."""
    ticket = get_ticket_or_404(db, ticket_id, user_id)
    db.delete(ticket)
    db.commit()
