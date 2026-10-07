import pytest
from fastapi.testclient import TestClient

TICKETS_URL = "/api/v1/tickets"
VEHICLES_URL = "/api/v1/vehicles"
TICKET = {
    "date": "2026-10-05",
    "vendor": "Gasolinera Sol",
    "category": "combustible",
    "net_amount": "41.32",
    "vat": "8.68",
    "total": "50.00",
}


def create_vehicle(client: TestClient, headers: dict[str, str]) -> int:
    """Crea un vehículo y devuelve su id."""
    vehicle = {"plate": "1234ABC", "brand": "Toyota", "model": "Prius"}
    return client.post(VEHICLES_URL, json=vehicle, headers=headers).json()["id"]


def test_create_ticket_returns_it_as_pending_review(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(TICKETS_URL, json=TICKET, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["date"] == "2026-10-05"
    assert body["vendor"] == "Gasolinera Sol"
    assert body["category"] == "combustible"
    assert body["net_amount"] == "41.32"
    assert body["vat"] == "8.68"
    assert body["total"] == "50.00"
    assert body["vehicle_id"] is None


def test_create_ticket_accepts_empty_draft(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(TICKETS_URL, json={}, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["date"] is None
    assert body["total"] is None


def test_create_ticket_ignores_status_sent_by_client(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        TICKETS_URL, json={**TICKET, "status": "confirmed"}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending_review"


def test_create_ticket_with_own_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.post(
        TICKETS_URL, json={**TICKET, "vehicle_id": vehicle_id}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["vehicle_id"] == vehicle_id


def test_create_ticket_with_vehicle_of_another_user_returns_404(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, other_auth_headers)

    response = client.post(
        TICKETS_URL, json={**TICKET, "vehicle_id": vehicle_id}, headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


@pytest.mark.parametrize(
    "category",
    [
        "combustible",
        "mantenimiento",
        "seguro",
        "limpieza",
        "reparaciones",
        "emisora",
        "autonomo",
        "datafono",
        "otros",
    ],
)
def test_create_ticket_accepts_every_allowed_category(
    client: TestClient, auth_headers: dict[str, str], category: str
) -> None:
    response = client.post(TICKETS_URL, json={"category": category}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["category"] == category


def test_create_ticket_rejects_unknown_category(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(TICKETS_URL, json={**TICKET, "category": "peajes"}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": "category: valor no permitido", "code": "validation_error"}


def test_create_ticket_rejects_negative_amount(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(TICKETS_URL, json={**TICKET, "total": "-5.00"}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "total: debe ser mayor o igual que 0",
        "code": "validation_error",
    }


def test_create_ticket_rejects_more_than_two_decimals(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(TICKETS_URL, json={**TICKET, "vat": "8.685"}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "vat: debe tener como máximo 2 decimales",
        "code": "validation_error",
    }


def test_create_ticket_rejects_invalid_date(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(TICKETS_URL, json={**TICKET, "date": "05/10/2026"}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "date: debe ser una fecha con formato AAAA-MM-DD",
        "code": "validation_error",
    }


def test_create_ticket_requires_authentication(client: TestClient) -> None:
    response = client.post(TICKETS_URL, json=TICKET)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
