from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import OdometerReading
from app.schemas.odometer import OdometerReadingCreate
from app.services.vehicle_service import get_vehicle_or_404


def create_reading(
    db: Session, user_id: int, vehicle_id: int, data: OdometerReadingCreate
) -> OdometerReading:
    """Registra una lectura de un vehículo del usuario, si encaja con las demás lecturas."""
    vehicle = get_vehicle_or_404(db, vehicle_id, user_id)
    _ensure_in_sequence(db, vehicle.id, data)

    reading = OdometerReading(user_id=user_id, vehicle_id=vehicle.id, **data.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def _ensure_in_sequence(db: Session, vehicle_id: int, data: OdometerReadingCreate) -> None:
    """Lanza 422 si la lectura rompe el orden: ordenadas por fecha, las lecturas nunca bajan.

    Se compara con la última lectura de los días anteriores y con la primera de los días
    posteriores. Las del mismo día no limitan: varias lecturas de un día se ordenan por km.
    """
    previous = _first_reading(
        db,
        OdometerReading.vehicle_id == vehicle_id,
        OdometerReading.date < data.date,
        newest_first=True,
    )
    if previous is not None and data.odometer_km < previous.odometer_km:
        raise _out_of_sequence("inferior a la anterior", previous)

    following = _first_reading(
        db,
        OdometerReading.vehicle_id == vehicle_id,
        OdometerReading.date > data.date,
        newest_first=False,
    )
    if following is not None and data.odometer_km > following.odometer_km:
        raise _out_of_sequence("superior a la posterior", following)


def _first_reading(
    db: Session, *conditions: ColumnElement[bool], newest_first: bool
) -> OdometerReading | None:
    """Devuelve la primera lectura que cumple las condiciones, en el orden indicado."""
    if newest_first:
        order = (OdometerReading.date.desc(), OdometerReading.odometer_km.desc())
    else:
        order = (OdometerReading.date.asc(), OdometerReading.odometer_km.asc())
    return db.scalars(select(OdometerReading).where(*conditions).order_by(*order).limit(1)).first()


def _out_of_sequence(problem: str, other: OdometerReading) -> ApiError:
    """Construye el error de lectura fuera de orden, citando la lectura con la que choca."""
    km = f"{other.odometer_km:,}".replace(",", ".")
    return ApiError(
        status_code=422,
        detail=f"La lectura no puede ser {problem}: {km} km el {other.date:%d/%m/%Y}",
        code="odometer_decreasing",
    )
