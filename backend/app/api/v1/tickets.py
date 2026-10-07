from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models import Ticket
from app.schemas.pagination import Page
from app.schemas.ticket import TicketCreate, TicketFilters, TicketRead, TicketUpdate
from app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=Page[TicketRead])
def list_tickets(
    filters: Annotated[TicketFilters, Query()], user: CurrentUser, db: DbSession
) -> Page[TicketRead]:
    """Lista los tickets del usuario autenticado, con filtros y paginación."""
    items, total = ticket_service.list_tickets(db, user.id, filters)
    return Page[TicketRead](items=items, total=total, page=filters.page, size=filters.size)


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(data: TicketCreate, user: CurrentUser, db: DbSession) -> Ticket:
    """Crea un ticket a mano para el usuario autenticado."""
    return ticket_service.create_ticket(db, user.id, data)


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, user: CurrentUser, db: DbSession) -> Ticket:
    """Devuelve un ticket del usuario autenticado."""
    return ticket_service.get_ticket_or_404(db, ticket_id, user.id)


@router.put("/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, data: TicketUpdate, user: CurrentUser, db: DbSession) -> Ticket:
    """Edita un ticket del usuario autenticado. El ticket queda pendiente de revisión."""
    return ticket_service.update_ticket(db, user.id, ticket_id, data)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, user: CurrentUser, db: DbSession) -> None:
    """Elimina un ticket del usuario autenticado."""
    ticket_service.delete_ticket(db, user.id, ticket_id)
