import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Ticket

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


def create_ticket(client: TestClient, headers: dict[str, str], **fields: object) -> int:
    """Crea un ticket con los campos indicados y devuelve su id."""
    return client.post(TICKETS_URL, json=fields, headers=headers).json()["id"]


def listed_ids(client: TestClient, headers: dict[str, str], query: str = "") -> list[int]:
    """Devuelve los ids del listado de tickets, en el orden recibido."""
    response = client.get(f"{TICKETS_URL}{query}", headers=headers)
    assert response.status_code == 200
    return [ticket["id"] for ticket in response.json()["items"]]


def test_list_returns_page_with_total(client: TestClient, auth_headers: dict[str, str]) -> None:
    for day in ("2026-10-01", "2026-10-02", "2026-10-03"):
        create_ticket(client, auth_headers, date=day)

    first = client.get(f"{TICKETS_URL}?size=2", headers=auth_headers).json()
    second = client.get(f"{TICKETS_URL}?size=2&page=2", headers=auth_headers).json()

    assert (first["total"], first["page"], first["size"]) == (3, 1, 2)
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert second["total"] == 3


def test_list_uses_default_page_size(client: TestClient, auth_headers: dict[str, str]) -> None:
    body = client.get(TICKETS_URL, headers=auth_headers).json()

    assert body == {"items": [], "total": 0, "page": 1, "size": 20}


def test_list_orders_by_date_descending_with_undated_last(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    undated = create_ticket(client, auth_headers)
    older = create_ticket(client, auth_headers, date="2026-09-01")
    newer = create_ticket(client, auth_headers, date="2026-10-01")

    assert listed_ids(client, auth_headers) == [newer, older, undated]


def test_list_returns_only_own_tickets(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    own = create_ticket(client, auth_headers)
    create_ticket(client, other_auth_headers)

    assert listed_ids(client, auth_headers) == [own]


def test_list_filters_by_date_range_inclusive(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_ticket(client, auth_headers, date="2026-09-30")
    first = create_ticket(client, auth_headers, date="2026-10-01")
    last = create_ticket(client, auth_headers, date="2026-10-31")
    create_ticket(client, auth_headers, date="2026-11-01")
    create_ticket(client, auth_headers)

    ids = listed_ids(client, auth_headers, "?date_from=2026-10-01&date_to=2026-10-31")

    assert ids == [last, first]


def test_list_filters_by_category(client: TestClient, auth_headers: dict[str, str]) -> None:
    fuel = create_ticket(client, auth_headers, category="combustible")
    create_ticket(client, auth_headers, category="limpieza")

    assert listed_ids(client, auth_headers, "?category=combustible") == [fuel]


def test_list_filters_by_status(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    confirmed = create_ticket(client, auth_headers)
    pending = create_ticket(client, auth_headers)
    db.execute(update(Ticket).where(Ticket.id == confirmed).values(status="confirmed"))

    assert listed_ids(client, auth_headers, "?status=confirmed") == [confirmed]
    assert listed_ids(client, auth_headers, "?status=pending_review") == [pending]


def test_list_filters_by_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    with_vehicle = create_ticket(client, auth_headers, vehicle_id=vehicle_id)
    create_ticket(client, auth_headers)

    assert listed_ids(client, auth_headers, f"?vehicle_id={vehicle_id}") == [with_vehicle]


def test_list_combines_filters(client: TestClient, auth_headers: dict[str, str]) -> None:
    match = create_ticket(client, auth_headers, date="2026-10-05", category="combustible")
    create_ticket(client, auth_headers, date="2026-10-05", category="limpieza")
    create_ticket(client, auth_headers, date="2026-09-05", category="combustible")

    ids = listed_ids(client, auth_headers, "?category=combustible&date_from=2026-10-01")

    assert ids == [match]


def test_list_with_vehicle_of_another_user_returns_nothing(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    foreign_vehicle = create_vehicle(client, other_auth_headers)
    create_ticket(client, other_auth_headers, vehicle_id=foreign_vehicle)

    assert listed_ids(client, auth_headers, f"?vehicle_id={foreign_vehicle}") == []


@pytest.mark.parametrize(
    ("query", "detail"),
    [
        ("?size=101", "size: debe ser menor o igual que 100"),
        ("?size=0", "size: debe ser mayor o igual que 1"),
        ("?page=0", "page: debe ser mayor o igual que 1"),
        ("?page=dos", "page: debe ser un número entero"),
        ("?category=peajes", "category: valor no permitido"),
        ("?status=borrado", "status: valor no permitido"),
        ("?date_from=01/10/2026", "date_from: debe ser una fecha con formato AAAA-MM-DD"),
    ],
)
def test_list_rejects_invalid_parameters(
    client: TestClient, auth_headers: dict[str, str], query: str, detail: str
) -> None:
    response = client.get(f"{TICKETS_URL}{query}", headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "code": "validation_error"}


def test_list_requires_authentication(client: TestClient) -> None:
    response = client.get(TICKETS_URL)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def confirm_in_db(db: Session, ticket_id: int) -> None:
    """Marca un ticket como confirmado directamente en la base de datos."""
    db.execute(update(Ticket).where(Ticket.id == ticket_id).values(status="confirmed"))


def test_get_returns_own_ticket(client: TestClient, auth_headers: dict[str, str]) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)

    response = client.get(f"{TICKETS_URL}/{ticket_id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == ticket_id
    assert body["vendor"] == "Gasolinera Sol"
    assert body["total"] == "50.00"


def test_update_replaces_ticket_data(client: TestClient, auth_headers: dict[str, str]) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)
    new_data = {**TICKET, "vendor": "Taller Paco", "category": "reparaciones", "total": "60.00"}

    response = client.put(f"{TICKETS_URL}/{ticket_id}", json=new_data, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["vendor"] == "Taller Paco"
    assert body["category"] == "reparaciones"
    assert body["total"] == "60.00"
    assert body["date"] == "2026-10-05"


def test_update_clears_fields_that_are_not_sent(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)

    response = client.put(
        f"{TICKETS_URL}/{ticket_id}", json={"vendor": "Taller Paco"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["vendor"] == "Taller Paco"
    assert body["total"] is None
    assert body["date"] is None


def test_update_returns_confirmed_ticket_to_pending_review(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)
    confirm_in_db(db, ticket_id)

    response = client.put(f"{TICKETS_URL}/{ticket_id}", json=TICKET, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "pending_review"


def test_update_rejects_vehicle_of_another_user(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)
    foreign_vehicle = create_vehicle(client, other_auth_headers)

    response = client.put(
        f"{TICKETS_URL}/{ticket_id}",
        json={**TICKET, "vehicle_id": foreign_vehicle},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


def test_update_rejects_invalid_data(client: TestClient, auth_headers: dict[str, str]) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)

    response = client.put(
        f"{TICKETS_URL}/{ticket_id}", json={**TICKET, "total": "-1.00"}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "total: debe ser mayor o igual que 0"


def test_delete_removes_own_ticket(client: TestClient, auth_headers: dict[str, str]) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)

    response = client.delete(f"{TICKETS_URL}/{ticket_id}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(f"{TICKETS_URL}/{ticket_id}", headers=auth_headers).status_code == 404


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_ticket_of_another_user_returns_404_and_is_untouched(
    client: TestClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    method: str,
) -> None:
    ticket_id = create_ticket(client, auth_headers, **TICKET)
    body = {"json": {"vendor": "Intruso"}} if method == "put" else {}

    response = client.request(
        method, f"{TICKETS_URL}/{ticket_id}", headers=other_auth_headers, **body
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket no encontrado", "code": "ticket_not_found"}
    own = client.get(f"{TICKETS_URL}/{ticket_id}", headers=auth_headers).json()
    assert own["vendor"] == "Gasolinera Sol"


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_unknown_ticket_returns_404(
    client: TestClient, auth_headers: dict[str, str], method: str
) -> None:
    body = {"json": TICKET} if method == "put" else {}

    response = client.request(method, f"{TICKETS_URL}/999999", headers=auth_headers, **body)

    assert response.status_code == 404
    assert response.json()["code"] == "ticket_not_found"


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_ticket_detail_requires_authentication(client: TestClient, method: str) -> None:
    body = {"json": TICKET} if method == "put" else {}

    response = client.request(method, f"{TICKETS_URL}/1", **body)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
