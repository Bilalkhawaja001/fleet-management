import os

from dotenv import load_dotenv

# Load .env early (dev convenience)
load_dotenv(override=True)


def _as_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    # Prefer PostgreSQL (set DATABASE_URL), fallback to sqlite for quick local run
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///fleet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security defaults (override via env in production)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _as_bool("SESSION_COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = _as_bool("REMEMBER_COOKIE_SECURE", False)

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # DB engine tuning
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Login brute-force protection
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # Document uploads
    DOCUMENT_ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp"}
    DOCUMENT_MAX_FILE_SIZE_MB = int(os.getenv("DOCUMENT_MAX_FILE_SIZE_MB", "10"))
    DOCUMENT_UPLOAD_BASE = os.getenv("DOCUMENT_UPLOAD_BASE", "uploads/trips")
