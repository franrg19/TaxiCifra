from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Vehicle
from app.schemas.vehicle import VehicleCreate


def list_vehicles(db: Session, user_id: int) -> Sequence[Vehicle]:
    """Devuelve los vehículos del usuario."""
    query = select(Vehicle).where(Vehicle.user_id == user_id).order_by(Vehicle.id)
    return db.scalars(query).all()


def create_vehicle(db: Session, user_id: int, data: VehicleCreate) -> Vehicle:
    """Da de alta un vehículo. La matrícula no puede repetirse en el mismo usuario."""
    duplicate = select(Vehicle).where(Vehicle.user_id == user_id, Vehicle.plate == data.plate)
    if db.scalar(duplicate) is not None:
        raise ApiError(
            status_code=409,
            detail="Ya tienes un vehículo con esa matrícula",
            code="plate_already_registered",
        )

    vehicle = Vehicle(user_id=user_id, **data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle
