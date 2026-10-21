from pathlib import Path
from uuid import uuid4

from app.core.config import settings

# Tamaño máximo de una imagen de ticket: 5 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# Primeros bytes ("firma") de cada formato admitido, con su tipo MIME y su extensión
SIGNATURES = {
    b"\xff\xd8\xff": ("image/jpeg", "jpg"),
    b"\x89PNG\r\n\x1a\n": ("image/png", "png"),
}


def detect_mime_type(data: bytes) -> str | None:
    """Devuelve el tipo real de la imagen según sus primeros bytes, o None si no se admite."""
    for signature, (mime_type, _) in SIGNATURES.items():
        if data.startswith(signature):
            return mime_type
    return None


def save_image(data: bytes, mime_type: str) -> str:
    """Guarda la imagen con un nombre aleatorio y devuelve ese nombre."""
    extension = next(ext for mime, ext in SIGNATURES.values() if mime == mime_type)
    filename = f"{uuid4().hex}.{extension}"
    path = image_location(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return filename


def image_location(filename: str) -> Path:
    """Devuelve la ruta en disco de una imagen guardada a partir de su nombre."""
    return Path(settings.images_dir) / filename


def delete_image(filename: str) -> None:
    """Borra una imagen guardada. Si ya no existe, no hace nada."""
    image_location(filename).unlink(missing_ok=True)
