from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """Parámetros de paginación comunes a todos los listados."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class Page[T](BaseModel):
    """Una página de resultados de un listado."""

    items: list[T]
    total: int
    page: int
    size: int
