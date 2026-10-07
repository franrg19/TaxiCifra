from sqlalchemy.orm import Session

from app.models import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate
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
