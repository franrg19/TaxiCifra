from pydantic import BaseModel


class Page[T](BaseModel):
    """Una página de resultados de un listado."""

    items: list[T]
    total: int
    page: int
    size: int
