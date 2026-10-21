import pytest
from fastapi.testclient import TestClient
from httpx import Response

VEHICLES_URL = "/api/v1/vehicles"


def create_vehicle(client: TestClient, headers: dict[str, str], plate: str = "1234ABC") -> int:
    """Crea un vehículo y devuelve su id."""
    vehicle = {"plate": plate, "brand": "Toyota", "model": "Prius"}
    return client.post(VEHICLES_URL, json=vehicle, headers=headers).json()["id"]


def odometer_url(vehicle_id: int) -> str:
    """Devuelve la ruta de las lecturas de un vehículo."""
    return f"{VEHICLES_URL}/{vehicle_id}/odometer"


def add_reading(
    client: TestClient, headers: dict[str, str], vehicle_id: int, day: str, km: int
) -> Response:
    """Registra una lectura y devuelve la respuesta."""
    reading = {"date": day, "odometer_km": km}
    return client.post(odometer_url(vehicle_id), json=reading, headers=headers)


@pytest.fixture
def vehicle_id(client: TestClient, auth_headers: dict[str, str]) -> int:
    """Vehículo del usuario principal."""
    return create_vehicle(client, auth_headers)


def test_create_reading_returns_it(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    response = add_reading(client, auth_headers, vehicle_id, "2026-10-20", 150000)

    assert response.status_code == 201
    body = response.json()
    assert body["vehicle_id"] == vehicle_id
    assert body["date"] == "2026-10-20"
    assert body["odometer_km"] == 150000
    assert "id" in body


def test_reading_can_equal_previous_one(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    add_reading(client, auth_headers, vehicle_id, "2026-10-20", 150000)

    response = add_reading(client, auth_headers, vehicle_id, "2026-10-21", 150000)

    assert response.status_code == 201


def test_reading_lower_than_previous_returns_422(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    add_reading(client, auth_headers, vehicle_id, "2026-10-20", 150000)

    response = add_reading(client, auth_headers, vehicle_id, "2026-10-21", 149999)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "La lectura no puede ser inferior a la anterior: 150.000 km el 20/10/2026",
        "code": "odometer_decreasing",
    }


def test_past_reading_must_fit_between_previous_and_next(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 100000)
    add_reading(client, auth_headers, vehicle_id, "2026-10-10", 102000)

    fits = add_reading(client, auth_headers, vehicle_id, "2026-10-05", 101000)
    too_high = add_reading(client, auth_headers, vehicle_id, "2026-10-06", 103000)

    assert fits.status_code == 201
    assert too_high.status_code == 422
    assert too_high.json() == {
        "detail": "La lectura no puede ser superior a la posterior: 102.000 km el 10/10/2026",
        "code": "odometer_decreasing",
    }


def test_several_readings_on_the_same_day_in_any_order(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    add_reading(client, auth_headers, vehicle_id, "2026-10-19", 100000)
    end_of_shift = add_reading(client, auth_headers, vehicle_id, "2026-10-20", 100300)

    # El inicio del turno se apunta después del final: también vale
    start_of_shift = add_reading(client, auth_headers, vehicle_id, "2026-10-20", 100050)

    assert end_of_shift.status_code == 201
    assert start_of_shift.status_code == 201


def test_readings_of_other_vehicles_do_not_limit(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    other_vehicle = create_vehicle(client, auth_headers, plate="9999ZZZ")
    add_reading(client, auth_headers, other_vehicle, "2026-10-01", 300000)

    response = add_reading(client, auth_headers, vehicle_id, "2026-10-20", 5000)

    assert response.status_code == 201


def test_reading_for_vehicle_of_another_user_returns_404(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    foreign_vehicle = create_vehicle(client, other_auth_headers)

    response = add_reading(client, auth_headers, foreign_vehicle, "2026-10-20", 1000)

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


@pytest.mark.parametrize(
    ("reading", "detail"),
    [
        ({"odometer_km": 1000}, "date: es obligatorio"),
        ({"date": "2026-10-20"}, "odometer_km: es obligatorio"),
        ({"date": "2026-10-20", "odometer_km": -1}, "odometer_km: debe ser mayor o igual que 0"),
        (
            {"date": "2026-10-20", "odometer_km": 10_000_000},
            "odometer_km: debe ser menor o igual que 9999999",
        ),
        ({"date": "2026-10-20", "odometer_km": 1000.5}, "odometer_km: debe ser un número entero"),
    ],
)
def test_create_reading_rejects_invalid_data(
    client: TestClient,
    auth_headers: dict[str, str],
    vehicle_id: int,
    reading: dict[str, object],
    detail: str,
) -> None:
    response = client.post(odometer_url(vehicle_id), json=reading, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "code": "validation_error"}


def test_create_reading_requires_authentication(client: TestClient) -> None:
    response = client.post(odometer_url(1), json={"date": "2026-10-20", "odometer_km": 1000})

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


# --- Listado ---


def listed_km(
    client: TestClient, headers: dict[str, str], vehicle_id: int, query: str = ""
) -> list[int]:
    """Devuelve los km del listado de lecturas, en el orden recibido."""
    response = client.get(f"{odometer_url(vehicle_id)}{query}", headers=headers)
    assert response.status_code == 200
    return [reading["odometer_km"] for reading in response.json()["items"]]


def test_list_returns_readings_newest_first(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 100000)
    add_reading(client, auth_headers, vehicle_id, "2026-10-20", 100300)
    add_reading(client, auth_headers, vehicle_id, "2026-10-20", 100050)

    assert listed_km(client, auth_headers, vehicle_id) == [100300, 100050, 100000]


def test_list_is_paginated(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    for day, km in (("2026-10-01", 100), ("2026-10-02", 200), ("2026-10-03", 300)):
        add_reading(client, auth_headers, vehicle_id, day, km)

    first = client.get(f"{odometer_url(vehicle_id)}?size=2", headers=auth_headers).json()

    assert (first["total"], first["page"], first["size"]) == (3, 1, 2)
    assert listed_km(client, auth_headers, vehicle_id, "?size=2&page=2") == [100]


def test_list_only_includes_readings_of_that_vehicle(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    other_vehicle = create_vehicle(client, auth_headers, plate="9999ZZZ")
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 1000)
    add_reading(client, auth_headers, other_vehicle, "2026-10-01", 5000)

    assert listed_km(client, auth_headers, vehicle_id) == [1000]


def test_list_rejects_invalid_page_size(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    response = client.get(f"{odometer_url(vehicle_id)}?size=101", headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"] == "size: debe ser menor o igual que 100"


# --- Borrado ---


def test_delete_removes_reading(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    reading_id = add_reading(client, auth_headers, vehicle_id, "2026-10-01", 1000).json()["id"]

    response = client.delete(f"{odometer_url(vehicle_id)}/{reading_id}", headers=auth_headers)

    assert response.status_code == 204
    assert listed_km(client, auth_headers, vehicle_id) == []


def test_delete_reading_through_another_vehicle_returns_404(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    other_vehicle = create_vehicle(client, auth_headers, plate="9999ZZZ")
    reading_id = add_reading(client, auth_headers, vehicle_id, "2026-10-01", 1000).json()["id"]

    response = client.delete(f"{odometer_url(other_vehicle)}/{reading_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Lectura no encontrada", "code": "reading_not_found"}
    assert listed_km(client, auth_headers, vehicle_id) == [1000]


def test_delete_unknown_reading_returns_404(
    client: TestClient, auth_headers: dict[str, str], vehicle_id: int
) -> None:
    response = client.delete(f"{odometer_url(vehicle_id)}/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "reading_not_found"


# --- Autorización ---


@pytest.mark.parametrize("method", ["get", "delete"])
def test_readings_of_another_user_return_404_and_are_untouched(
    client: TestClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    vehicle_id: int,
    method: str,
) -> None:
    reading_id = add_reading(client, auth_headers, vehicle_id, "2026-10-01", 1000).json()["id"]
    url = odometer_url(vehicle_id) + (f"/{reading_id}" if method == "delete" else "")

    response = client.request(method, url, headers=other_auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"
    assert listed_km(client, auth_headers, vehicle_id) == [1000]


@pytest.mark.parametrize(("method", "path"), [("get", ""), ("delete", "/1")])
def test_list_and_delete_require_authentication(client: TestClient, method: str, path: str) -> None:
    response = client.request(method, f"{odometer_url(1)}{path}")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
