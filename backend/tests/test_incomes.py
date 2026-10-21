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


# --- Listado ---


def create_income(client: TestClient, headers: dict[str, str], **fields: object) -> int:
    """Crea un ingreso (con los datos de INCOME y los indicados) y devuelve su id."""
    return client.post(INCOMES_URL, json={**INCOME, **fields}, headers=headers).json()["id"]


def listed_ids(client: TestClient, headers: dict[str, str], query: str = "") -> list[int]:
    """Devuelve los ids del listado de ingresos, en el orden recibido."""
    response = client.get(f"{INCOMES_URL}{query}", headers=headers)
    assert response.status_code == 200
    return [income["id"] for income in response.json()["items"]]


def test_list_returns_page_with_total(client: TestClient, auth_headers: dict[str, str]) -> None:
    for day in ("2026-10-01", "2026-10-02", "2026-10-03"):
        create_income(client, auth_headers, date=day)

    first = client.get(f"{INCOMES_URL}?size=2", headers=auth_headers).json()
    second = client.get(f"{INCOMES_URL}?size=2&page=2", headers=auth_headers).json()

    assert (first["total"], first["page"], first["size"]) == (3, 1, 2)
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1


def test_list_uses_default_page_size(client: TestClient, auth_headers: dict[str, str]) -> None:
    body = client.get(INCOMES_URL, headers=auth_headers).json()

    assert body == {"items": [], "total": 0, "page": 1, "size": 20}


def test_list_orders_by_date_descending(client: TestClient, auth_headers: dict[str, str]) -> None:
    older = create_income(client, auth_headers, date="2026-09-01")
    newer = create_income(client, auth_headers, date="2026-10-01")
    same_day_later = create_income(client, auth_headers, date="2026-10-01")

    assert listed_ids(client, auth_headers) == [same_day_later, newer, older]


def test_list_returns_only_own_incomes(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    own = create_income(client, auth_headers)
    create_income(client, other_auth_headers)

    assert listed_ids(client, auth_headers) == [own]


def test_list_filters_by_date_range_inclusive(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create_income(client, auth_headers, date="2026-09-30")
    first = create_income(client, auth_headers, date="2026-10-01")
    last = create_income(client, auth_headers, date="2026-10-31")
    create_income(client, auth_headers, date="2026-11-01")

    ids = listed_ids(client, auth_headers, "?date_from=2026-10-01&date_to=2026-10-31")

    assert ids == [last, first]


def test_list_filters_by_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    with_vehicle = create_income(client, auth_headers, vehicle_id=vehicle_id)
    create_income(client, auth_headers)

    assert listed_ids(client, auth_headers, f"?vehicle_id={vehicle_id}") == [with_vehicle]


def test_list_with_vehicle_of_another_user_returns_nothing(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    foreign_vehicle = create_vehicle(client, other_auth_headers)
    create_income(client, other_auth_headers, vehicle_id=foreign_vehicle)

    assert listed_ids(client, auth_headers, f"?vehicle_id={foreign_vehicle}") == []


@pytest.mark.parametrize(
    ("query", "detail"),
    [
        ("?size=101", "size: debe ser menor o igual que 100"),
        ("?page=0", "page: debe ser mayor o igual que 1"),
        ("?date_to=31/10/2026", "date_to: debe ser una fecha con formato AAAA-MM-DD"),
    ],
)
def test_list_rejects_invalid_parameters(
    client: TestClient, auth_headers: dict[str, str], query: str, detail: str
) -> None:
    response = client.get(f"{INCOMES_URL}{query}", headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "code": "validation_error"}


def test_list_requires_authentication(client: TestClient) -> None:
    response = client.get(INCOMES_URL)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


# --- Edición y borrado ---


def test_update_replaces_income_data(client: TestClient, auth_headers: dict[str, str]) -> None:
    income_id = create_income(client, auth_headers)
    new_data = {"date": "2026-10-21", "amount": "200.00"}

    response = client.put(f"{INCOMES_URL}/{income_id}", json=new_data, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["date"] == "2026-10-21"
    assert body["amount"] == "200.00"
    assert body["description"] is None


def test_update_validates_like_creation(client: TestClient, auth_headers: dict[str, str]) -> None:
    income_id = create_income(client, auth_headers)

    response = client.put(
        f"{INCOMES_URL}/{income_id}", json={**INCOME, "amount": "0"}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "amount: debe ser mayor que 0"


def test_update_rejects_vehicle_of_another_user(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    income_id = create_income(client, auth_headers)
    foreign_vehicle = create_vehicle(client, other_auth_headers)

    response = client.put(
        f"{INCOMES_URL}/{income_id}",
        json={**INCOME, "vehicle_id": foreign_vehicle},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


def test_delete_removes_own_income(client: TestClient, auth_headers: dict[str, str]) -> None:
    income_id = create_income(client, auth_headers)

    response = client.delete(f"{INCOMES_URL}/{income_id}", headers=auth_headers)

    assert response.status_code == 204
    assert listed_ids(client, auth_headers) == []


@pytest.mark.parametrize("method", ["put", "delete"])
def test_income_of_another_user_returns_404_and_is_untouched(
    client: TestClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    method: str,
) -> None:
    income_id = create_income(client, auth_headers)
    body = {"json": {**INCOME, "amount": "1.00"}} if method == "put" else {}

    response = client.request(
        method, f"{INCOMES_URL}/{income_id}", headers=other_auth_headers, **body
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingreso no encontrado", "code": "income_not_found"}
    own = client.get(INCOMES_URL, headers=auth_headers).json()["items"]
    assert [income["amount"] for income in own] == ["185.50"]


@pytest.mark.parametrize("method", ["put", "delete"])
def test_unknown_income_returns_404(
    client: TestClient, auth_headers: dict[str, str], method: str
) -> None:
    body = {"json": INCOME} if method == "put" else {}

    response = client.request(method, f"{INCOMES_URL}/999999", headers=auth_headers, **body)

    assert response.status_code == 404
    assert response.json()["code"] == "income_not_found"


@pytest.mark.parametrize("method", ["put", "delete"])
def test_income_detail_requires_authentication(client: TestClient, method: str) -> None:
    body = {"json": INCOME} if method == "put" else {}

    response = client.request(method, f"{INCOMES_URL}/1", **body)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
