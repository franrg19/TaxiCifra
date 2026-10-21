import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OdometerReading(Base):
    """Lectura del cuentakilómetros de un vehículo en una fecha."""

    __tablename__ = "odometer_readings"
    __table_args__ = (Index("ix_odometer_readings_vehicle_id_date", "vehicle_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Las lecturas no tienen sentido sin su vehículo: se borran con él
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    date: Mapped[dt.date] = mapped_column(Date)
    odometer_km: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
