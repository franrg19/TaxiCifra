from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación leída de variables de entorno (o de .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    images_dir: str = "uploads"
    jwt_secret: str
    jwt_expire_hours: int = 24
    # Único origen desde el que un navegador puede llamar a la API (CORS)
    frontend_origin: str = "http://localhost:5173"
    # Sin clave de Anthropic se usa el proveedor OCR simulado
    anthropic_api_key: str | None = None
    ocr_model: str = "claude-haiku-5-5"


settings = Settings()
