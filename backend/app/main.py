from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import auth, dashboard, incomes, odometer, tickets, vehicles
from app.core.config import settings

# Motivo en español por tipo de error de Pydantic (el resto: "valor no válido")
VALIDATION_MESSAGES = {
    "missing": "es obligatorio",
    "string_too_short": "debe tener al menos {min_length} caracteres",
    "string_too_long": "debe tener como máximo {max_length} caracteres",
    "enum": "valor no permitido",
    "greater_than": "debe ser mayor que {gt}",
    "greater_than_equal": "debe ser mayor o igual que {ge}",
    "less_than_equal": "debe ser menor o igual que {le}",
    "int_parsing": "debe ser un número entero",
    "int_from_float": "debe ser un número entero",
    "decimal_max_places": "debe tener como máximo {decimal_places} decimales",
    "decimal_parsing": "debe ser un número",
    "date_from_datetime_parsing": "debe ser una fecha con formato AAAA-MM-DD",
}

app = FastAPI(title="Taxicifra API")

# Solo el frontend puede llamar a la API desde un navegador. El token va en la cabecera
# Authorization (no en cookies), así que no hacen falta credenciales CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(vehicles.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(incomes.router, prefix="/api/v1")
app.include_router(odometer.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


def _validation_message(error: dict[str, Any]) -> str:
    """Convierte un error de validación en un texto 'campo: motivo'."""
    template = VALIDATION_MESSAGES.get(error["type"], "valor no válido")
    return f"{error['loc'][-1]}: {template.format(**error.get('ctx', {}))}"


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Devuelve todos los errores HTTP con el formato uniforme detail + code."""
    code = getattr(exc, "code", "http_error")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": code})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Devuelve los errores de validación de entrada con el formato uniforme."""
    detail = "; ".join(_validation_message(error) for error in exc.errors())
    return JSONResponse(status_code=422, content={"detail": detail, "code": "validation_error"})
