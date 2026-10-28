from fastapi.testclient import TestClient
from httpx import Response

from app.main import app

client = TestClient(app)


def test_app_starts_and_exposes_openapi() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Taxicifra API"


def preflight(origin: str) -> Response:
    """Simula la consulta previa (OPTIONS) que hace el navegador antes de llamar a la API."""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    }
    return client.options("/api/v1/vehicles", headers=headers)


def test_cors_allows_the_frontend_origin() -> None:
    response = preflight("http://localhost:5173")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_other_origins() -> None:
    response = preflight("https://web-maliciosa.example")

    assert "access-control-allow-origin" not in response.headers
