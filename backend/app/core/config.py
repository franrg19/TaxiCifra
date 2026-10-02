from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación leída de variables de entorno (o de .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    images_dir: str = "uploads"
    jwt_secret: str
    jwt_expire_hours: int = 24


settings = Settings()
