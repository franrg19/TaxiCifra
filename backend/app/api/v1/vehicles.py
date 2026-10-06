from collections.abc import Sequence

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.models import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleRead])
def list_vehicles(user: CurrentUser, db: DbSession) -> Sequence[Vehicle]:
    """Lista los vehículos del usuario autenticado."""
    return vehicle_service.list_vehicles(db, user.id)


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(data: VehicleCreate, user: CurrentUser, db: DbSession) -> Vehicle:
    """Da de alta un vehículo del usuario autenticado."""
    return vehicle_service.create_vehicle(db, user.id, data)


@router.put("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int, data: VehicleUpdate, user: CurrentUser, db: DbSession
) -> Vehicle:
    """Edita un vehículo del usuario autenticado."""
    return vehicle_service.update_vehicle(db, user.id, vehicle_id, data)
