import datetime as dt

import pytest
from fastapi.testclient import TestClient

SUMMARY_URL = "/api/v1/dashboard/summary"
TICKETS_URL = "/api/v1/tickets"
INCOMES_URL = "/api/v1/incomes"
VEHICLES_URL = "/api/v1/vehicles"


def create_vehicle(client: TestClient, headers: dict[str, str], plate: str = "1234ABC") -> int:
    """Crea un vehículo y devuelve su id."""
    vehicle = {"plate": plate, "brand": "Toyota", "model": "Prius"}
    return client.post(VEHICLES_URL, json=vehicle, headers=headers).json()["id"]


def add_ticket(
    client: TestClient,
    headers: dict[str, str],
    total: str,
    day: str = "2026-10-15",
    vehicle_id: int | None = None,
    confirm: bool = True,
) -> None:
    """Crea un ticket con base + IVA que cuadra con el total y, por defecto, lo confirma."""
    ticket = {
        "date": day,
        "vendor": "Gasolinera Sol",
        "category": "combustible",
        "net_amount": total,
        "vat": "0.00",
        "total": total,
        "vehicle_id": vehicle_id,
    }
    ticket_id = client.post(TICKETS_URL, json=ticket, headers=headers).json()["id"]
    if confirm:
        client.post(f"{TICKETS_URL}/{ticket_id}/confirm", headers=headers)


def add_income(
    client: TestClient,
    headers: dict[str, str],
    amount: str,
    day: str = "2026-10-15",
    vehicle_id: int | None = None,
) -> None:
    """Registra un ingreso."""
    income = {"date": day, "amount": amount, "vehicle_id": vehicle_id}
    client.post(INCOMES_URL, json=income, headers=headers)


def add_reading(
    client: TestClient, headers: dict[str, str], vehicle_id: int, day: str, km: int
) -> None:
    """Registra una lectura del cuentakilómetros."""
    reading = {"date": day, "odometer_km": km}
    client.post(f"{VEHICLES_URL}/{vehicle_id}/odometer", json=reading, headers=headers)


def summary(client: TestClient, headers: dict[str, str], query: str = "") -> dict[str, object]:
    """Pide el resumen del dashboard y lo devuelve."""
    response = client.get(f"{SUMMARY_URL}{query}", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_summary_without_data_returns_zeros_and_no_km_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert summary(client, auth_headers) == {
        "expenses": "0.00",
        "incomes": "0.00",
        "profit": "0.00",
        "ticket_count": 0,
        "km_driven": None,
        "cost_per_km": None,
    }


def test_summary_only_counts_confirmed_tickets(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    add_ticket(client, auth_headers, "50.00")
    add_ticket(client, auth_headers, "30.25")
    add_ticket(client, auth_headers, "999.00", confirm=False)

    body = summary(client, auth_headers)

    assert body["expenses"] == "80.25"
    assert body["ticket_count"] == 2


def test_summary_profit_is_incomes_minus_expenses(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    add_ticket(client, auth_headers, "80.25")
    add_income(client, auth_headers, "150.00")
    add_income(client, auth_headers, "50.50")

    body = summary(client, auth_headers)

    assert body["incomes"] == "200.50"
    assert body["profit"] == "120.25"


def test_summary_profit_can_be_negative(client: TestClient, auth_headers: dict[str, str]) -> None:
    add_ticket(client, auth_headers, "300.00")
    add_income(client, auth_headers, "100.00")

    assert summary(client, auth_headers)["profit"] == "-200.00"


def test_summary_filters_by_period_inclusive(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for day in ("2026-09-30", "2026-10-01", "2026-10-31", "2026-11-01"):
        add_ticket(client, auth_headers, "10.00", day=day)
        add_income(client, auth_headers, "100.00", day=day)

    body = summary(client, auth_headers, "?date_from=2026-10-01&date_to=2026-10-31")

    assert body["expenses"] == "20.00"
    assert body["incomes"] == "200.00"
    assert body["ticket_count"] == 2


def test_summary_filters_by_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_ticket(client, auth_headers, "40.00", vehicle_id=vehicle_id)
    add_ticket(client, auth_headers, "10.00")
    add_income(client, auth_headers, "100.00", vehicle_id=vehicle_id)
    add_income(client, auth_headers, "60.00")

    body = summary(client, auth_headers, f"?vehicle_id={vehicle_id}")

    assert body["expenses"] == "40.00"
    assert body["incomes"] == "100.00"
    assert body["ticket_count"] == 1


def test_km_driven_is_last_minus_first_reading_of_the_period(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_reading(client, auth_headers, vehicle_id, "2026-09-30", 99000)
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 100000)
    add_reading(client, auth_headers, vehicle_id, "2026-10-15", 101200)
    add_reading(client, auth_headers, vehicle_id, "2026-10-31", 102500)
    add_reading(client, auth_headers, vehicle_id, "2026-11-01", 102600)

    body = summary(client, auth_headers, "?date_from=2026-10-01&date_to=2026-10-31")

    assert body["km_driven"] == 2500


def test_km_driven_adds_up_every_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    first = create_vehicle(client, auth_headers, "1111AAA")
    second = create_vehicle(client, auth_headers, "2222BBB")
    add_reading(client, auth_headers, first, "2026-10-01", 1000)
    add_reading(client, auth_headers, first, "2026-10-31", 1500)
    add_reading(client, auth_headers, second, "2026-10-01", 50000)
    add_reading(client, auth_headers, second, "2026-10-31", 50300)

    assert summary(client, auth_headers)["km_driven"] == 800
    assert summary(client, auth_headers, f"?vehicle_id={second}")["km_driven"] == 300


def test_vehicle_with_a_single_reading_does_not_add_km(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = create_vehicle(client, auth_headers, "1111AAA")
    second = create_vehicle(client, auth_headers, "2222BBB")
    add_reading(client, auth_headers, first, "2026-10-01", 1000)
    add_reading(client, auth_headers, first, "2026-10-31", 1500)
    add_reading(client, auth_headers, second, "2026-10-15", 50000)

    assert summary(client, auth_headers)["km_driven"] == 500


def test_cost_per_km_is_expenses_divided_by_km_with_three_decimals(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 100000)
    add_reading(client, auth_headers, vehicle_id, "2026-10-31", 100300)
    add_ticket(client, auth_headers, "38.00")

    body = summary(client, auth_headers)

    # 38 / 300 = 0,12666... → 0,127
    assert body["cost_per_km"] == "0.127"


def test_cost_per_km_without_two_readings_is_no_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 100000)
    add_ticket(client, auth_headers, "38.00")

    body = summary(client, auth_headers)

    assert body["km_driven"] is None
    assert body["cost_per_km"] is None


def test_cost_per_km_with_zero_km_is_no_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_reading(client, auth_headers, vehicle_id, "2026-10-01", 100000)
    add_reading(client, auth_headers, vehicle_id, "2026-10-02", 100000)
    add_ticket(client, auth_headers, "38.00")

    body = summary(client, auth_headers)

    assert body["km_driven"] == 0
    assert body["cost_per_km"] is None


def test_summary_ignores_data_of_other_users(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    other_vehicle = create_vehicle(client, other_auth_headers)
    add_ticket(client, other_auth_headers, "50.00", vehicle_id=other_vehicle)
    add_income(client, other_auth_headers, "100.00", vehicle_id=other_vehicle)
    add_reading(client, other_auth_headers, other_vehicle, "2026-10-01", 1000)
    add_reading(client, other_auth_headers, other_vehicle, "2026-10-31", 2000)

    empty = summary(client, auth_headers)
    foreign_vehicle = summary(client, auth_headers, f"?vehicle_id={other_vehicle}")

    for body in (empty, foreign_vehicle):
        assert body["expenses"] == "0.00"
        assert body["incomes"] == "0.00"
        assert body["km_driven"] is None


@pytest.mark.parametrize(
    ("query", "detail"),
    [
        ("?date_from=01/10/2026", "date_from: debe ser una fecha con formato AAAA-MM-DD"),
        ("?vehicle_id=uno", "vehicle_id: debe ser un número entero"),
    ],
)
def test_summary_rejects_invalid_parameters(
    client: TestClient, auth_headers: dict[str, str], query: str, detail: str
) -> None:
    response = client.get(f"{SUMMARY_URL}{query}", headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "code": "validation_error"}


def test_summary_requires_authentication(client: TestClient) -> None:
    response = client.get(SUMMARY_URL)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


# --- Gasto por categoría ---

BY_CATEGORY_URL = "/api/v1/dashboard/by-category"
MONTHLY_URL = "/api/v1/dashboard/monthly"


def add_categorized_ticket(
    client: TestClient,
    headers: dict[str, str],
    category: str,
    total: str,
    day: str = "2026-10-15",
    confirm: bool = True,
) -> None:
    """Crea un ticket de una categoría y, por defecto, lo confirma."""
    ticket = {
        "date": day,
        "vendor": "Proveedor",
        "category": category,
        "net_amount": total,
        "vat": "0.00",
        "total": total,
    }
    ticket_id = client.post(TICKETS_URL, json=ticket, headers=headers).json()["id"]
    if confirm:
        client.post(f"{TICKETS_URL}/{ticket_id}/confirm", headers=headers)


def by_category(client: TestClient, headers: dict[str, str], query: str = "") -> list[object]:
    """Pide el gasto por categoría y lo devuelve."""
    response = client.get(f"{BY_CATEGORY_URL}{query}", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_by_category_groups_confirmed_expenses_from_highest_to_lowest(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    add_categorized_ticket(client, auth_headers, "combustible", "50.00")
    add_categorized_ticket(client, auth_headers, "combustible", "45.50")
    add_categorized_ticket(client, auth_headers, "seguro", "120.00")
    add_categorized_ticket(client, auth_headers, "limpieza", "15.00")
    add_categorized_ticket(client, auth_headers, "reparaciones", "500.00", confirm=False)

    assert by_category(client, auth_headers) == [
        {"category": "seguro", "total": "120.00"},
        {"category": "combustible", "total": "95.50"},
        {"category": "limpieza", "total": "15.00"},
    ]


def test_by_category_without_expenses_is_empty(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert by_category(client, auth_headers) == []


def test_by_category_filters_by_period_and_vehicle(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_ticket(client, auth_headers, "40.00", day="2026-10-15", vehicle_id=vehicle_id)
    add_ticket(client, auth_headers, "10.00", day="2026-10-15")
    add_ticket(client, auth_headers, "99.00", day="2026-09-15", vehicle_id=vehicle_id)

    query = f"?date_from=2026-10-01&date_to=2026-10-31&vehicle_id={vehicle_id}"

    assert by_category(client, auth_headers, query) == [
        {"category": "combustible", "total": "40.00"}
    ]


def test_by_category_ignores_other_users(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    add_ticket(client, other_auth_headers, "50.00")

    assert by_category(client, auth_headers) == []


# --- Evolución mensual ---


def monthly(client: TestClient, headers: dict[str, str], query: str = "") -> list[dict]:
    """Pide la evolución mensual y la devuelve."""
    response = client.get(f"{MONTHLY_URL}{query}", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_monthly_always_returns_the_twelve_months(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    months = monthly(client, auth_headers, "?year=2026")

    assert [month["month"] for month in months] == list(range(1, 13))
    assert months[0] == {"month": 1, "expenses": "0.00", "incomes": "0.00", "profit": "0.00"}


def test_monthly_puts_each_amount_in_its_month(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    add_ticket(client, auth_headers, "50.00", day="2026-10-01")
    add_ticket(client, auth_headers, "30.00", day="2026-10-31")
    add_ticket(client, auth_headers, "999.00", day="2026-10-15", confirm=False)
    add_income(client, auth_headers, "200.00", day="2026-10-20")
    add_income(client, auth_headers, "150.00", day="2026-03-05")

    months = monthly(client, auth_headers, "?year=2026")

    assert months[9] == {"month": 10, "expenses": "80.00", "incomes": "200.00", "profit": "120.00"}
    assert months[2] == {"month": 3, "expenses": "0.00", "incomes": "150.00", "profit": "150.00"}


def test_monthly_only_includes_the_requested_year(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    add_ticket(client, auth_headers, "50.00", day="2025-10-15")
    add_income(client, auth_headers, "100.00", day="2027-01-15")

    months = monthly(client, auth_headers, "?year=2026")

    assert all(month["expenses"] == "0.00" for month in months)
    assert all(month["incomes"] == "0.00" for month in months)


def test_monthly_uses_current_year_by_default(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    today = dt.date.today()
    add_income(client, auth_headers, "100.00", day=today.isoformat())

    months = monthly(client, auth_headers)

    assert months[today.month - 1]["incomes"] == "100.00"


def test_monthly_filters_by_vehicle(client: TestClient, auth_headers: dict[str, str]) -> None:
    vehicle_id = create_vehicle(client, auth_headers)
    add_income(client, auth_headers, "100.00", day="2026-10-15", vehicle_id=vehicle_id)
    add_income(client, auth_headers, "60.00", day="2026-10-15")

    months = monthly(client, auth_headers, f"?year=2026&vehicle_id={vehicle_id}")

    assert months[9]["incomes"] == "100.00"


def test_monthly_ignores_other_users(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    add_income(client, other_auth_headers, "100.00", day="2026-10-15")

    months = monthly(client, auth_headers, "?year=2026")

    assert months[9]["incomes"] == "0.00"


@pytest.mark.parametrize(
    ("query", "detail"),
    [
        ("?year=1999", "year: debe ser mayor o igual que 2000"),
        ("?year=2101", "year: debe ser menor o igual que 2100"),
        ("?year=dosmil", "year: debe ser un número entero"),
    ],
)
def test_monthly_rejects_invalid_year(
    client: TestClient, auth_headers: dict[str, str], query: str, detail: str
) -> None:
    response = client.get(f"{MONTHLY_URL}{query}", headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "code": "validation_error"}


@pytest.mark.parametrize("url", [BY_CATEGORY_URL, MONTHLY_URL])
def test_dashboard_endpoints_require_authentication(client: TestClient, url: str) -> None:
    response = client.get(url)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
