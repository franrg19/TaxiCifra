import pytest
from fastapi.testclient import TestClient

INCOMES_URL = "/api/v1/incomes"
VEHICLES_URL = "/api/v1/vehicles"
INCOME = {"date": "2026-10-20", "amount": "185.50", "description": "Recaudación del día"}


def create_vehicle(client: TestClient, headers: dict[str, str]) -> int:
    """Crea un vehículo y devuelve su id."""
    vehicle = {"plate": "1234ABC", "brand": "Toyota", "model": "Prius"}
    return client.post(VEHICLES_URL, json=vehicle, headers=headers).json()["id"]


def test_create_income_returns_it(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(INCOMES_URL, json=INCOME, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["date"] == "2026-10-20"
    assert body["amount"] == "185.50"
    assert body["description"] == "Recaudación del día"
    assert body["vehicle_id"] is None
    assert "id" in body


def test_create_income_without_description(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        INCOMES_URL, json={"date": "2026-10-20", "amount": "90"}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_income_with_own_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)

    response = client.post(
        INCOMES_URL, json={**INCOME, "vehicle_id": vehicle_id}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["vehicle_id"] == vehicle_id


def test_create_income_with_vehicle_of_another_user_returns_404(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, other_auth_headers)

    response = client.post(
        INCOMES_URL, json={**INCOME, "vehicle_id": vehicle_id}, headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


@pytest.mark.parametrize("field", ["date", "amount"])
def test_create_income_requires_date_and_amount(
    client: TestClient, auth_headers: dict[str, str], field: str
) -> None:
    data = {key: value for key, value in INCOME.items() if key != field}

    response = client.post(INCOMES_URL, json=data, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": f"{field}: es obligatorio", "code": "validation_error"}


@pytest.mark.parametrize("amount", ["0", "-10.00"])
def test_create_income_rejects_amount_not_greater_than_zero(
    client: TestClient, auth_headers: dict[str, str], amount: str
) -> None:
    response = client.post(INCOMES_URL, json={**INCOME, "amount": amount}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"] == "amount: debe ser mayor que 0"


def test_create_income_rejects_more_than_two_decimals(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(INCOMES_URL, json={**INCOME, "amount": "10.555"}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"] == "amount: debe tener como máximo 2 decimales"


@pytest.mark.parametrize("description", ["", "x" * 256])
def test_create_income_rejects_invalid_description(
    client: TestClient, auth_headers: dict[str, str], description: str
) -> None:
    response = client.post(
        INCOMES_URL, json={**INCOME, "description": description}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_create_income_accepts_description_of_max_length(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        INCOMES_URL, json={**INCOME, "description": "x" * 255}, headers=auth_headers
    )

    assert response.status_code == 201


def test_create_income_requires_authentication(client: TestClient) -> None:
    response = client.post(INCOMES_URL, json=INCOME)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
