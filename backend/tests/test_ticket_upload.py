from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.api.deps import get_ocr_provider
from app.core.config import settings
from app.main import app
from app.services.image_storage import MAX_IMAGE_SIZE
from app.services.ocr.base import ExtractedTicket

UPLOAD_URL = "/api/v1/tickets/upload"
TICKETS_URL = "/api/v1/tickets"

# Contenido mínimo con la firma de cada formato: basta para que se reconozca el tipo real
JPEG = b"\xff\xd8\xff\xe0" + b"foto de ticket"
PNG = b"\x89PNG\r\n\x1a\n" + b"foto de ticket"


@pytest.fixture(autouse=True)
def images_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Guarda las imágenes de los tests en una carpeta temporal, no en el volumen real."""
    monkeypatch.setattr(settings, "images_dir", str(tmp_path))
    return tmp_path


def upload(
    client: TestClient,
    headers: dict[str, str],
    content: bytes = JPEG,
    filename: str = "ticket.jpg",
    content_type: str = "image/jpeg",
) -> Response:
    """Sube una imagen de ticket y devuelve la respuesta."""
    files = {"image": (filename, content, content_type)}
    return client.post(UPLOAD_URL, files=files, headers=headers)


def test_upload_creates_pending_ticket_with_ocr_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = upload(client, auth_headers)

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


def test_upload_saves_image_with_random_name(
    client: TestClient, auth_headers: dict[str, str], images_dir: Path
) -> None:
    upload(client, auth_headers, filename="../../malicioso.jpg")

    saved = list(images_dir.iterdir())
    assert len(saved) == 1
    assert saved[0].suffix == ".jpg"
    assert "malicioso" not in saved[0].name
    assert saved[0].read_bytes() == JPEG


def test_upload_accepts_png(
    client: TestClient, auth_headers: dict[str, str], images_dir: Path
) -> None:
    response = upload(client, auth_headers, PNG, "ticket.png", "image/png")

    assert response.status_code == 201
    assert [file.suffix for file in images_dir.iterdir()] == [".png"]


@pytest.mark.parametrize("content", [b"esto es texto, no una foto", b""])
def test_upload_rejects_content_that_is_not_jpg_or_png(
    client: TestClient, auth_headers: dict[str, str], images_dir: Path, content: bytes
) -> None:
    # El nombre y el tipo declarados dicen JPG, pero el contenido real no lo es
    response = upload(client, auth_headers, content)

    assert response.status_code == 415
    assert response.json() == {
        "detail": "La imagen debe ser JPG o PNG",
        "code": "unsupported_image_type",
    }
    assert list(images_dir.iterdir()) == []


def test_upload_accepts_image_of_exactly_max_size(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    content = JPEG + b"0" * (MAX_IMAGE_SIZE - len(JPEG))

    response = upload(client, auth_headers, content)

    assert response.status_code == 201


def test_upload_rejects_image_over_max_size(
    client: TestClient, auth_headers: dict[str, str], images_dir: Path
) -> None:
    content = JPEG + b"0" * (MAX_IMAGE_SIZE - len(JPEG) + 1)

    response = upload(client, auth_headers, content)

    assert response.status_code == 413
    assert response.json() == {
        "detail": "La imagen no puede superar 5 MB",
        "code": "image_too_large",
    }
    assert list(images_dir.iterdir()) == []


def test_upload_requires_image(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(UPLOAD_URL, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_upload_requires_authentication(client: TestClient, images_dir: Path) -> None:
    response = upload(client, {})

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert list(images_dir.iterdir()) == []


def test_uploaded_ticket_is_only_visible_to_its_owner(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    ticket_id = upload(client, auth_headers).json()["id"]

    own = client.get(f"{TICKETS_URL}/{ticket_id}", headers=auth_headers)
    other = client.get(f"{TICKETS_URL}/{ticket_id}", headers=other_auth_headers)

    assert own.status_code == 200
    assert other.status_code == 404


def test_uploaded_ticket_can_be_confirmed(client: TestClient, auth_headers: dict[str, str]) -> None:
    ticket_id = upload(client, auth_headers).json()["id"]

    response = client.post(f"{TICKETS_URL}/{ticket_id}/confirm", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


# --- Tolerancia a fallos del OCR ---


class FailingOcrProvider:
    """Proveedor que siempre falla, como un servicio caído o sin conexión."""

    def extract(self, image: bytes, mime_type: str) -> ExtractedTicket:
        raise TimeoutError("El proveedor no responde")


class FixedOcrProvider:
    """Proveedor que devuelve los datos indicados, aunque sean incorrectos."""

    def __init__(self, extracted: ExtractedTicket) -> None:
        self.extracted = extracted

    def extract(self, image: bytes, mime_type: str) -> ExtractedTicket:
        return self.extracted


def use_ocr(provider: object) -> None:
    """Hace que la API use este proveedor OCR en lugar del simulado (lo deshace `client`)."""
    app.dependency_overrides[get_ocr_provider] = lambda: provider


def test_ocr_failure_still_creates_empty_ticket_with_image(
    client: TestClient, auth_headers: dict[str, str], images_dir: Path
) -> None:
    use_ocr(FailingOcrProvider())

    response = upload(client, auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_review"
    for field in ("date", "vendor", "category", "net_amount", "vat", "total"):
        assert body[field] is None
    assert len(list(images_dir.iterdir())) == 1


def test_ocr_partial_read_keeps_what_was_read(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    use_ocr(FixedOcrProvider(ExtractedTicket(total="50.00")))

    body = upload(client, auth_headers).json()

    assert body["total"] == "50.00"
    assert body["vendor"] is None
    assert body["date"] is None


def test_ocr_unknown_category_is_left_empty(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    use_ocr(FixedOcrProvider(ExtractedTicket(vendor="Repsol", category="gasolina")))

    body = upload(client, auth_headers).json()

    assert body["category"] is None
    assert body["vendor"] == "Repsol"


@pytest.mark.parametrize("amount", ["-5.00", "12.345", "123456789.00"])
def test_ocr_invalid_amount_is_left_empty(
    client: TestClient, auth_headers: dict[str, str], amount: str
) -> None:
    # Negativo, con más de dos decimales y demasiado grande para la columna
    use_ocr(FixedOcrProvider(ExtractedTicket(net_amount=amount, vat="8.68", total="50.00")))

    body = upload(client, auth_headers).json()

    assert body["net_amount"] is None
    assert body["vat"] == "8.68"
    assert body["total"] == "50.00"


@pytest.mark.parametrize("vendor", ["", "x" * 101])
def test_ocr_invalid_vendor_is_left_empty(
    client: TestClient, auth_headers: dict[str, str], vendor: str
) -> None:
    use_ocr(FixedOcrProvider(ExtractedTicket(vendor=vendor, total="50.00")))

    body = upload(client, auth_headers).json()

    assert body["vendor"] is None
    assert body["total"] == "50.00"


def test_ticket_from_failed_ocr_can_be_completed_and_confirmed(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    use_ocr(FailingOcrProvider())
    ticket_id = upload(client, auth_headers).json()["id"]
    reviewed = {
        "date": "2026-10-05",
        "vendor": "Gasolinera Sol",
        "category": "combustible",
        "net_amount": "41.32",
        "vat": "8.68",
        "total": "50.00",
    }

    client.put(f"{TICKETS_URL}/{ticket_id}", json=reviewed, headers=auth_headers)
    response = client.post(f"{TICKETS_URL}/{ticket_id}/confirm", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


# --- Ver la imagen ---


def image_url(ticket_id: int) -> str:
    """Devuelve la ruta de la imagen de un ticket."""
    return f"{TICKETS_URL}/{ticket_id}/image"


@pytest.mark.parametrize(
    ("content", "filename", "content_type"),
    [(JPEG, "ticket.jpg", "image/jpeg"), (PNG, "ticket.png", "image/png")],
)
def test_get_image_returns_uploaded_photo(
    client: TestClient,
    auth_headers: dict[str, str],
    content: bytes,
    filename: str,
    content_type: str,
) -> None:
    ticket_id = upload(client, auth_headers, content, filename, content_type).json()["id"]

    response = client.get(image_url(ticket_id), headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == content_type
    assert response.content == content


def test_get_image_of_manual_ticket_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    ticket_id = client.post(TICKETS_URL, json={}, headers=auth_headers).json()["id"]

    response = client.get(image_url(ticket_id), headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "El ticket no tiene imagen", "code": "image_not_found"}


def test_get_image_missing_on_disk_returns_404(
    client: TestClient, auth_headers: dict[str, str], images_dir: Path
) -> None:
    ticket_id = upload(client, auth_headers).json()["id"]
    for file in images_dir.iterdir():
        file.unlink()

    response = client.get(image_url(ticket_id), headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "image_not_found"


def test_get_image_of_another_user_returns_404(
    client: TestClient, auth_headers: dict[str, str], other_auth_headers: dict[str, str]
) -> None:
    ticket_id = upload(client, auth_headers).json()["id"]

    response = client.get(image_url(ticket_id), headers=other_auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "ticket_not_found"


def test_get_image_of_unknown_ticket_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get(image_url(999999), headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "ticket_not_found"


def test_get_image_requires_authentication(client: TestClient) -> None:
    response = client.get(image_url(1))

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
