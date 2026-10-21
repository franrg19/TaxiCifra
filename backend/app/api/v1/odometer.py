from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.models import OdometerReading
from app.schemas.odometer import OdometerReadingCreate, OdometerReadingRead
from app.services import odometer_service

router = APIRouter(prefix="/vehicles/{vehicle_id}/odometer", tags=["odometer"])


@router.post("", response_model=OdometerReadingRead, status_code=status.HTTP_201_CREATED)
def create_reading(
    vehicle_id: int, data: OdometerReadingCreate, user: CurrentUser, db: DbSession
) -> OdometerReading:
    """Registra una lectura del cuentakilómetros de un vehículo del usuario autenticado."""
    return odometer_service.create_reading(db, user.id, vehicle_id, data)
