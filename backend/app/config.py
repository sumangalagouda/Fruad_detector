import os
from pathlib import Path
from dotenv import load_dotenv

# Locate base directory and load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "fintelligence_flask_session_secret_key_2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fintelligence_jwt_super_secret_key_2026")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24 hours

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:sumangala@localhost:3306/fintelligence"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    # Uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 25))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # CORS
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]

    # AI Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
