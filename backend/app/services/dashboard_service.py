import datetime as dt
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models import Income, OdometerReading, Ticket, TicketStatus
from app.schemas.dashboard import (
    CategoryExpense,
    DashboardFilters,
    DashboardSummary,
    MonthlyFilters,
    MonthlyTotals,
)

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")
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


def get_by_category(db: Session, user_id: int, filters: DashboardFilters) -> list[CategoryExpense]:
    """Gasto confirmado por categoría, de mayor a menor. Solo aparecen las que tienen gasto."""
    total = func.sum(Ticket.total)
    query = (
        select(Ticket.category, total)
        .where(Ticket.status == TicketStatus.CONFIRMED, *_conditions(Ticket, user_id, filters))
        .group_by(Ticket.category)
        .order_by(total.desc(), Ticket.category)
    )
    return [
        CategoryExpense(category=category, total=amount.quantize(CENTS))
        for category, amount in db.execute(query)
    ]


def get_monthly(db: Session, user_id: int, filters: MonthlyFilters) -> list[MonthlyTotals]:
    """Gastos confirmados, ingresos y beneficio de cada mes del año (siempre los 12 meses)."""
    year = DashboardFilters(
        date_from=dt.date(filters.year, 1, 1),
        date_to=dt.date(filters.year, 12, 31),
        vehicle_id=filters.vehicle_id,
    )
    expenses = _sum_by_month(
        db,
        Ticket.total,
        Ticket.date,
        [Ticket.status == TicketStatus.CONFIRMED, *_conditions(Ticket, user_id, year)],
    )
    incomes = _sum_by_month(db, Income.amount, Income.date, _conditions(Income, user_id, year))

    # SQL solo devuelve los meses con datos; los demás se completan a cero
    months = []
    for month in range(1, 13):
        month_expenses = expenses.get(month, ZERO)
        month_incomes = incomes.get(month, ZERO)
        months.append(
            MonthlyTotals(
                month=month,
                expenses=month_expenses,
                incomes=month_incomes,
                profit=month_incomes - month_expenses,
            )
        )
    return months


def _sum_by_month(
    db: Session,
    amount: InstrumentedAttribute[Decimal | None],
    date: InstrumentedAttribute[dt.date | None],
    conditions: list[ColumnElement[bool]],
) -> dict[int, Decimal]:
    """Suma de importes agrupada por mes: {número de mes: total}."""
    month = func.extract("month", date)
    query = select(month, func.sum(amount)).where(*conditions).group_by(month)
    return {int(number): total.quantize(CENTS) for number, total in db.execute(query)}


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
