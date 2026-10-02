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
