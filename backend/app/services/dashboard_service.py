from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.models import Income, OdometerReading, Ticket, TicketStatus
from app.schemas.dashboard import DashboardFilters, DashboardSummary

CENTS = Decimal("0.01")
# El coste por km de un taxi ronda los céntimos: se da con tres decimales (0,127 €/km)
COST_PER_KM_PRECISION = Decimal("0.001")


def get_summary(db: Session, user_id: int, filters: DashboardFilters) -> DashboardSummary:
    """Calcula gastos, ingresos, beneficio, tickets, km y coste por km del periodo."""
    expenses, ticket_count = _expenses_and_ticket_count(db, user_id, filters)
    incomes = _incomes(db, user_id, filters)
    km_driven = _km_driven(db, user_id, filters)

    return DashboardSummary(
        expenses=expenses,
        incomes=incomes,
        profit=incomes - expenses,
        ticket_count=ticket_count,
        km_driven=km_driven,
        cost_per_km=_cost_per_km(expenses, km_driven),
    )


def _conditions(
    model: type[Ticket] | type[Income] | type[OdometerReading],
    user_id: int,
    filters: DashboardFilters,
) -> list[ColumnElement[bool]]:
    """Condiciones comunes: datos del usuario, dentro del periodo y, si se pide, del vehículo."""
    conditions = [model.user_id == user_id]
    if filters.date_from is not None:
        conditions.append(model.date >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(model.date <= filters.date_to)
    if filters.vehicle_id is not None:
        conditions.append(model.vehicle_id == filters.vehicle_id)
    return conditions


def _expenses_and_ticket_count(
    db: Session, user_id: int, filters: DashboardFilters
) -> tuple[Decimal, int]:
    """Suma y número de tickets confirmados. Los pendientes de revisión NUNCA cuentan."""
    query = select(func.coalesce(func.sum(Ticket.total), 0), func.count(Ticket.id)).where(
        Ticket.status == TicketStatus.CONFIRMED, *_conditions(Ticket, user_id, filters)
    )
    total, count = db.execute(query).one()
    return Decimal(total).quantize(CENTS), count


def _incomes(db: Session, user_id: int, filters: DashboardFilters) -> Decimal:
    """Suma de los ingresos del periodo."""
    query = select(func.coalesce(func.sum(Income.amount), 0)).where(
        *_conditions(Income, user_id, filters)
    )
    return Decimal(db.scalar(query)).quantize(CENTS)


def _km_driven(db: Session, user_id: int, filters: DashboardFilters) -> int | None:
    """Km recorridos en el periodo: suma de los km de cada vehículo, o None si no hay datos.

    Las lecturas de un vehículo nunca bajan (se valida al registrarlas), así que
    "última - primera lectura del periodo" es lo mismo que MAX(km) - MIN(km).
    Un vehículo con menos de dos lecturas en el periodo no suma.
    """
    km_per_vehicle = (
        select(
            (func.max(OdometerReading.odometer_km) - func.min(OdometerReading.odometer_km)).label(
                "km"
            )
        )
        .where(*_conditions(OdometerReading, user_id, filters))
        .group_by(OdometerReading.vehicle_id)
        .having(func.count() >= 2)
        .subquery()
    )
    # SUM de ninguna fila es NULL: sin vehículos con dos lecturas, "sin datos"
    return db.scalar(select(func.sum(km_per_vehicle.c.km)))


def _cost_per_km(expenses: Decimal, km_driven: int | None) -> Decimal | None:
    """Gastos / km, o None si no hay km. NUNCA divide entre cero."""
    if not km_driven:
        return None
    return (expenses / km_driven).quantize(COST_PER_KM_PRECISION, rounding=ROUND_HALF_UP)
