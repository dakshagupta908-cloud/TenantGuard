import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

_root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if _root_env.exists():
    load_dotenv(dotenv_path=_root_env, override=False)
else:
    load_dotenv(override=False)

INSECURE_DEFAULT_KEYS = {
    "",
    "dev-only-secret-key-change-me-in-production-0123456789",
    "change-this-to-a-secure-random-64-char-hex-string-in-production",
    "docker-dev-secret-key-replace-in-prod-9876543210",
}


class Settings:
    def __init__(self) -> None:
        self.APP_NAME: str = os.getenv("APP_NAME", "TenantGuard")
        self.APP_ENV: str = os.getenv("APP_ENV", "development").lower()
        self.SECRET_KEY: str = os.getenv(
            "SECRET_KEY", "dev-only-secret-key-change-me-in-production-0123456789"
        )
        if self.APP_ENV == "production" and (
            self.SECRET_KEY in INSECURE_DEFAULT_KEYS or len(self.SECRET_KEY) < 32
        ):
            raise RuntimeError(
                "FATAL SECURITY CONFIG: APP_ENV is 'production' but SECRET_KEY is set to a default "
                "or short value (<32 chars). Set a strong random SECRET_KEY before starting."
            )

        self.ADMIN_EMAIL: str = (
            os.getenv("ADMIN_EMAIL", "admin@example.com").lower().strip()
        )
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        )
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite:///./tenantguard.db"
        )
        self.AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock").lower()
        self.OPENAI_API_BASE: str = os.getenv(
            "OPENAI_API_BASE", "https://api.openai.com/v1"
        )
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.EMBEDDING_MODEL: str = os.getenv(
            "EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self.MIN_SIMILARITY_THRESHOLD: float = float(
            os.getenv("MIN_SIMILARITY_THRESHOLD", "0.18")
        )
        self.TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "4"))
        self.RATE_LIMIT_PER_MINUTE: int = int(
            os.getenv("RATE_LIMIT_PER_MINUTE", "60")
        )
        cors_raw = os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        )
        self.CORS_ORIGINS: List[str] = [
            origin.strip() for origin in cors_raw.split(",") if origin.strip()
        ]
        self.SMTP_HOST: str = os.getenv("SMTP_HOST", "")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
        self.SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
        self.SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
        self.SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")


settings = Settings()
