from collections.abc import Sequence

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Ticket, Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def get_vehicle_or_404(db: Session, vehicle_id: int, user_id: int) -> Vehicle:
    """Devuelve el vehículo si existe y es del usuario; si no, responde 404."""
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.user_id != user_id:
        raise ApiError(status_code=404, detail="Vehículo no encontrado", code="vehicle_not_found")
    return vehicle


def _ensure_plate_is_free(
    db: Session, user_id: int, plate: str, ignore_vehicle_id: int | None = None
) -> None:
    """Responde 409 si el usuario ya tiene otro vehículo con esa matrícula."""
    query = select(Vehicle).where(Vehicle.user_id == user_id, Vehicle.plate == plate)
    if ignore_vehicle_id is not None:
        query = query.where(Vehicle.id != ignore_vehicle_id)
    if db.scalar(query) is not None:
        raise ApiError(
            status_code=409,
            detail="Ya tienes un vehículo con esa matrícula",
            code="plate_already_registered",
        )


def list_vehicles(db: Session, user_id: int) -> Sequence[Vehicle]:
    """Devuelve los vehículos del usuario."""
    query = select(Vehicle).where(Vehicle.user_id == user_id).order_by(Vehicle.id)
    return db.scalars(query).all()


def create_vehicle(db: Session, user_id: int, data: VehicleCreate) -> Vehicle:
    """Da de alta un vehículo. La matrícula no puede repetirse en el mismo usuario."""
    _ensure_plate_is_free(db, user_id, data.plate)

    vehicle = Vehicle(user_id=user_id, **data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def update_vehicle(db: Session, user_id: int, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
    """Reemplaza los datos de un vehículo del usuario."""
    vehicle = get_vehicle_or_404(db, vehicle_id, user_id)
    _ensure_plate_is_free(db, user_id, data.plate, ignore_vehicle_id=vehicle.id)

    vehicle.plate = data.plate
    vehicle.brand = data.brand
    vehicle.model = data.model
    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, user_id: int, vehicle_id: int, force: bool = False) -> None:
    """Elimina un vehículo del usuario.

    Si tiene tickets asociados responde 409, salvo que se indique force. Con force, el
    vehículo se borra y sus tickets se conservan sin vehículo (lo hace la clave foránea,
    definida con ON DELETE SET NULL).
    """
    vehicle = get_vehicle_or_404(db, vehicle_id, user_id)

    has_tickets = db.scalar(select(exists().where(Ticket.vehicle_id == vehicle.id)))
    if has_tickets and not force:
        raise ApiError(
            status_code=409,
            detail="El vehículo tiene tickets asociados. Confirma el borrado para eliminarlo: "
            "sus tickets se conservarán sin vehículo",
            code="vehicle_has_related_data",
        )

    db.delete(vehicle)
    db.commit()
