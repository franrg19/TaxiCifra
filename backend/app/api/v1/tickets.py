from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.models import Ticket
from app.schemas.ticket import TicketCreate, TicketRead
from app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(data: TicketCreate, user: CurrentUser, db: DbSession) -> Ticket:
    """Crea un ticket a mano para el usuario autenticado."""
    return ticket_service.create_ticket(db, user.id, data)
