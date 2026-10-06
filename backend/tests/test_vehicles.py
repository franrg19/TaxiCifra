from fastapi.testclient import TestClient

VEHICLES_URL = "/api/v1/vehicles"
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
