"""Configuración por variables de entorno (secrets nunca hardcodeados)."""
from __future__ import annotations

from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - fallback si no está instalado aún
    BaseSettings = object  # type: ignore
    SettingsConfigDict = dict  # type: ignore


class Settings(BaseSettings):  # type: ignore[misc]
    # --- Base de datos ---
    database_url: str = "postgresql+asyncpg://sueldoclaro:sueldoclaro@localhost:5432/sueldoclaro"
    # URL síncrona para Alembic
    database_url_sync: str = "postgresql+psycopg://sueldoclaro:sueldoclaro@localhost:5432/sueldoclaro"

    # --- Redis (refresh tokens / rate limit). Vacío = fallback en memoria ---
    redis_url: str = ""

    # --- Seguridad ---
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 15 * 60          # 15 minutos
    refresh_token_ttl_seconds: int = 7 * 24 * 3600   # 7 días

    # --- App ---
    rate_limit_por_minuto: int = 120
    env: str = "dev"

    model_config = SettingsConfigDict(env_prefix="SUELDOCLARO_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> "Settings":
    return Settings()  # type: ignore[call-arg]
