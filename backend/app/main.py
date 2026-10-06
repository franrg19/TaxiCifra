from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import auth, vehicles

# Motivo en español por tipo de error de Pydantic (el resto: "valor no válido")
VALIDATION_MESSAGES = {
    "missing": "es obligatorio",
    "string_too_short": "debe tener al menos {min_length} caracteres",
    "string_too_long": "debe tener como máximo {max_length} caracteres",
}

app = FastAPI(title="Taxicifra API")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(vehicles.router, prefix="/api/v1")


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
