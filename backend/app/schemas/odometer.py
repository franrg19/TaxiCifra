import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class OdometerReadingCreate(BaseModel):
    """Datos de entrada para registrar una lectura del cuentakilómetros."""

    date: dt.date
    odometer_km: int = Field(ge=0, le=9_999_999)


class OdometerReadingRead(BaseModel):
    """Datos de la lectura que devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    date: dt.date
    odometer_km: int
    created_at: dt.datetime
