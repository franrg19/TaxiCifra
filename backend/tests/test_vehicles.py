from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Income, OdometerReading, Ticket

VEHICLES_URL = "/api/v1/vehicles"
TICKETS_URL = "/api/v1/tickets"
INCOMES_URL = "/api/v1/incomes"
VEHICLE = {"plate": "1234 abc", "brand": "Toyota", "model": "Prius"}
NOT_AUTHENTICATED = {"detail": "No autenticado", "code": "not_authenticated"}


def test_create_vehicle_returns_it_with_normalized_plate(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(VEHICLES_URL, json=VEHICLE, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["plate"] == "1234ABC"
    assert body["brand"] == "Toyota"
    assert body["model"] == "Prius"
    assert "id" in body


def test_list_returns_only_own_vehicles(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    client.post(VEHICLES_URL, json=VEHICLE, headers=auth_headers)
    client.post(VEHICLES_URL, json={**VEHICLE, "plate": "9999ZZZ"}, headers=other_auth_headers)

    response = client.get(VEHICLES_URL, headers=auth_headers)

    assert response.status_code == 200
    assert [vehicle["plate"] for vehicle in response.json()] == ["1234ABC"]


def test_create_rejects_duplicate_plate_for_same_user(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post(VEHICLES_URL, json=VEHICLE, headers=auth_headers)

    response = client.post(
        VEHICLES_URL, json={**VEHICLE, "plate": "1234-ABC"}, headers=auth_headers
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Ya tienes un vehículo con esa matrícula",
        "code": "plate_already_registered",
    }


def test_create_allows_same_plate_for_another_user(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    client.post(VEHICLES_URL, json=VEHICLE, headers=auth_headers)

    response = client.post(VEHICLES_URL, json=VEHICLE, headers=other_auth_headers)

    assert response.status_code == 201


def test_create_rejects_plate_without_characters(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(VEHICLES_URL, json={**VEHICLE, "plate": " - "}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": "plate: valor no válido", "code": "validation_error"}


def test_vehicles_require_authentication(client: TestClient) -> None:
    list_response = client.get(VEHICLES_URL)
    create_response = client.post(VEHICLES_URL, json=VEHICLE)

    assert list_response.status_code == 401
    assert list_response.json() == NOT_AUTHENTICATED
    assert create_response.status_code == 401
    assert create_response.json() == NOT_AUTHENTICATED


def create_vehicle(client: TestClient, headers: dict[str, str], plate: str = "1234ABC") -> int:
    """Crea un vehículo y devuelve su id."""
    response = client.post(VEHICLES_URL, json={**VEHICLE, "plate": plate}, headers=headers)
    return response.json()["id"]


def test_update_replaces_vehicle_data(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    new_data = {"plate": "5678 def", "brand": "Skoda", "model": "Octavia"}

    response = client.put(f"{VEHICLES_URL}/{vehicle_id}", json=new_data, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == vehicle_id
    assert body["plate"] == "5678DEF"
    assert body["brand"] == "Skoda"
    assert body["model"] == "Octavia"


def test_update_allows_keeping_the_same_plate(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.put(
        f"{VEHICLES_URL}/{vehicle_id}", json={**VEHICLE, "model": "Corolla"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["model"] == "Corolla"


def test_update_rejects_plate_of_another_own_vehicle(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_vehicle(client, auth_headers, plate="1234ABC")
    second_id = create_vehicle(client, auth_headers, plate="5678DEF")

    response = client.put(
        f"{VEHICLES_URL}/{second_id}", json={**VEHICLE, "plate": "1234ABC"}, headers=auth_headers
    )

    assert response.status_code == 409
    assert response.json()["code"] == "plate_already_registered"


def test_update_vehicle_of_another_user_returns_404(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.put(f"{VEHICLES_URL}/{vehicle_id}", json=VEHICLE, headers=other_auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Vehículo no encontrado", "code": "vehicle_not_found"}


def test_update_unknown_vehicle_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.put(f"{VEHICLES_URL}/999999", json=VEHICLE, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


def test_update_requires_authentication(client: TestClient) -> None:
    response = client.put(f"{VEHICLES_URL}/1", json=VEHICLE)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED


def test_delete_removes_own_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(VEHICLES_URL, headers=auth_headers).json() == []


def test_delete_vehicle_of_another_user_returns_404_and_keeps_it(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}", headers=other_auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"
    assert len(client.get(VEHICLES_URL, headers=auth_headers).json()) == 1


def test_delete_unknown_vehicle_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.delete(f"{VEHICLES_URL}/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


def test_delete_requires_authentication(client: TestClient) -> None:
    response = client.delete(f"{VEHICLES_URL}/1")

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED


def create_ticket_for_vehicle(client: TestClient, headers: dict[str, str], vehicle_id: int) -> int:
    """Crea un ticket asociado al vehículo y devuelve su id."""
    response = client.post(TICKETS_URL, json={"vehicle_id": vehicle_id}, headers=headers)
    return response.json()["id"]


def test_delete_vehicle_with_tickets_returns_409_and_keeps_it(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    create_ticket_for_vehicle(client, auth_headers, vehicle_id)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["code"] == "vehicle_has_related_data"
    assert len(client.get(VEHICLES_URL, headers=auth_headers).json()) == 1


def test_force_delete_removes_vehicle_and_keeps_its_tickets_without_vehicle(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    ticket_id = create_ticket_for_vehicle(client, auth_headers, vehicle_id)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}?force=true", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(VEHICLES_URL, headers=auth_headers).json() == []
    remaining = db.execute(select(Ticket.id, Ticket.vehicle_id)).all()
    assert remaining == [(ticket_id, None)]


def test_force_delete_works_for_vehicle_without_tickets(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}?force=true", headers=auth_headers)

    assert response.status_code == 204


def create_income_for_vehicle(client: TestClient, headers: dict[str, str], vehicle_id: int) -> int:
    """Crea un ingreso asociado al vehículo y devuelve su id."""
    income = {"date": "2026-10-20", "amount": "100.00", "vehicle_id": vehicle_id}
    return client.post(INCOMES_URL, json=income, headers=headers).json()["id"]


def test_delete_vehicle_with_incomes_returns_409_and_keeps_it(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    create_income_for_vehicle(client, auth_headers, vehicle_id)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["code"] == "vehicle_has_related_data"
    assert len(client.get(VEHICLES_URL, headers=auth_headers).json()) == 1


def test_force_delete_keeps_incomes_without_vehicle(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    income_id = create_income_for_vehicle(client, auth_headers, vehicle_id)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}?force=true", headers=auth_headers)

    assert response.status_code == 204
    remaining = db.execute(select(Income.id, Income.vehicle_id)).all()
    assert remaining == [(income_id, None)]


def add_reading_to_vehicle(client: TestClient, headers: dict[str, str], vehicle_id: int) -> None:
    """Registra una lectura de km del vehículo."""
    reading = {"date": "2026-10-20", "odometer_km": 150000}
    client.post(f"{VEHICLES_URL}/{vehicle_id}/odometer", json=reading, headers=headers)


def test_delete_vehicle_with_readings_returns_409_and_keeps_it(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_reading_to_vehicle(client, auth_headers, vehicle_id)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["code"] == "vehicle_has_related_data"


def test_force_delete_removes_vehicle_readings(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_reading_to_vehicle(client, auth_headers, vehicle_id)

    response = client.delete(f"{VEHICLES_URL}/{vehicle_id}?force=true", headers=auth_headers)

    assert response.status_code == 204
    assert db.scalars(select(OdometerReading)).all() == []
