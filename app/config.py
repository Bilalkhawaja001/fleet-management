import os

from dotenv import load_dotenv

# Load .env early (dev convenience)
load_dotenv(override=True)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    # Prefer PostgreSQL (set DATABASE_URL), fallback to sqlite for quick local run
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///fleet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
