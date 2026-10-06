import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VehicleCreate(BaseModel):
    """Datos de entrada para dar de alta un vehículo."""

    plate: str = Field(min_length=1, max_length=15)
    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, value: str) -> str:
        """Deja la matrícula en mayúsculas y sin espacios ni guiones."""
        plate = re.sub(r"[\s-]", "", value).upper()
        if not plate:
            raise ValueError("matrícula vacía")
        return plate


class VehicleUpdate(VehicleCreate):
    """Datos de entrada para editar un vehículo (se reemplazan todos los campos)."""


class VehicleRead(BaseModel):
    """Datos del vehículo que devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plate: str
    brand: str
    model: str
    created_at: datetime
