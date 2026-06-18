"""Configuração da aplicação via pydantic-settings (prefixo de env `APP_`)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente / arquivo `.env`."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    app_name: str = "micro-expressions-utility"
    api_v1_prefix: str = "/api/v1"

    # SQLite em dev; mesmo schema migra para PostgreSQL em prod (JSON salvo como TEXT).
    database_url: str = "sqlite:///./data/app.db"

    # Vídeos vivem no filesystem; o banco guarda só o caminho.
    upload_dir: Path = Path("data/uploads")
    # Artefatos intermediários do pipeline (audio.wav, transcript.json, signals.json...).
    job_work_dir: Path = Path("data/jobs")

    # Limites de upload (questionário: 200 MB / 30 min).
    max_upload_bytes: int = 200 * 1024 * 1024
    max_duration_seconds: int = 30 * 60
    allowed_content_types: tuple[str, ...] = ("video/mp4", "video/quicktime", "video/webm")

    # Pipeline de processamento.
    # False (padrão) usa os dublês determinísticos; True usa OpenCV/MediaPipe/Whisper reais.
    use_real_pipeline: bool = False
    whisper_model: str = "base"
    ollama_url: str = "http://localhost:11434"
    # Orçamento de tokens do LLM: acima disso, comprime o contexto (sumarização hierárquica).
    max_context_tokens: int = 7500

    # Fila / workers.
    job_timeout_seconds: int = 30 * 60
    max_retries: int = 3
    retry_backoff_seconds: tuple[int, ...] = (2, 5, 10)

    # Auth básica (dev). Em produção, sobrescrever via env e usar senhas fortes.
    auth_username: str = "vendedor"
    auth_password: str = "changeme"
    auth_secret: str = "dev-secret-change-me"
    auth_token_ttl_seconds: int = 8 * 60 * 60

    # CORS (frontend Next.js).
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)

    # Retenção: apaga vídeos do disco após N dias.
    retention_days: int = 7


@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações em cache (instância única por processo)."""
    return Settings()
