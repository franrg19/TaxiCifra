import datetime as dt
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TicketStatus(StrEnum):
    """Estados de un ticket. Solo los confirmados cuentan como gasto."""

    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"


class TicketCategory(StrEnum):
    """Categorías de gasto permitidas."""

    COMBUSTIBLE = "combustible"
    MANTENIMIENTO = "mantenimiento"
    SEGURO = "seguro"
    LIMPIEZA = "limpieza"
    REPARACIONES = "reparaciones"
    EMISORA = "emisora"
    AUTONOMO = "autonomo"
    DATAFONO = "datafono"
    OTROS = "otros"


class Ticket(Base):
    """Ticket de gasto. Los campos de contenido pueden estar vacíos hasta que se confirma."""

    __tablename__ = "tickets"
    __table_args__ = (Index("ix_tickets_user_id_date", "user_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id", ondelete="SET NULL"))
    date: Mapped[dt.date | None] = mapped_column(Date)
    vendor: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(20))
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    vat: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    image_path: Mapped[str | None] = mapped_column(String(255))
    ocr_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=TicketStatus.PENDING_REVIEW)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
