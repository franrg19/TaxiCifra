from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models import OdometerReading
from app.schemas.odometer import OdometerReadingCreate, OdometerReadingRead
from app.schemas.pagination import Page, PageParams
from app.services import odometer_service

router = APIRouter(prefix="/vehicles/{vehicle_id}/odometer", tags=["odometer"])


@router.get("", response_model=Page[OdometerReadingRead])
def list_readings(
    vehicle_id: int, params: Annotated[PageParams, Query()], user: CurrentUser, db: DbSession
) -> Page[OdometerReadingRead]:
    """Lista las lecturas de un vehículo del usuario autenticado, con paginación."""
    items, total = odometer_service.list_readings(db, user.id, vehicle_id, params)
    return Page[OdometerReadingRead](items=items, total=total, page=params.page, size=params.size)


@router.post("", response_model=OdometerReadingRead, status_code=status.HTTP_201_CREATED)
def create_reading(
    vehicle_id: int, data: OdometerReadingCreate, user: CurrentUser, db: DbSession
) -> OdometerReading:
    """Registra una lectura del cuentakilómetros de un vehículo del usuario autenticado."""
    return odometer_service.create_reading(db, user.id, vehicle_id, data)


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading(vehicle_id: int, reading_id: int, user: CurrentUser, db: DbSession) -> None:
    """Elimina una lectura de un vehículo del usuario autenticado."""
    odometer_service.delete_reading(db, user.id, vehicle_id, reading_id)
