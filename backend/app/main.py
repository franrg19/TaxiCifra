from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import auth

app = FastAPI(title="TaxiGest API")

app.include_router(auth.router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Devuelve todos los errores HTTP con el formato uniforme detail + code."""
    code = getattr(exc, "code", "http_error")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": code})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Devuelve los errores de validación de entrada con el formato uniforme."""
    fields = ", ".join(str(error["loc"][-1]) for error in exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": f"Datos no válidos en: {fields}", "code": "validation_error"},
    )
