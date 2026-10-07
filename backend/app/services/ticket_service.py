from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate, TicketFilters
from app.services.vehicle_service import get_vehicle_or_404


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
