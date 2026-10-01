from fastapi import HTTPException


class ApiError(HTTPException):
    """Error de negocio con el formato uniforme de la API: detail + code."""

    def __init__(self, status_code: int, detail: str, code: str) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
