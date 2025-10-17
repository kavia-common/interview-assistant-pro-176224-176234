import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load variables from .env if present; actual env is prioritized
load_dotenv()


@dataclass
class Config:
    DB_TYPE: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    JWT_SECRET: str
    CORS_ORIGINS: str
    PORT: int


def _int(env_name: str, default: int) -> int:
    try:
        return int(os.getenv(env_name, default))
    except Exception:
        return default


# PUBLIC_INTERFACE
def get_config() -> Config:
    """Return loaded configuration from environment variables.
    Expected environment variables:
      - DB_HOST, DB_PORT (default 5000), DB_USER, DB_PASSWORD, DB_NAME
      - JWT_SECRET
      - CORS_ORIGINS (comma-separated or single origin, default http://localhost:3000)
      - PORT (backend port, default 3001)
    """
    return Config(
        DB_TYPE=os.getenv("DB_TYPE", "mysql"),
        DB_HOST=os.getenv("DB_HOST", "localhost"),
        DB_PORT=_int("DB_PORT", 5000),  # per acceptance criteria note
        DB_NAME=os.getenv("DB_NAME", "interview_assistant"),
        DB_USER=os.getenv("DB_USER", "root"),
        DB_PASSWORD=os.getenv("DB_PASSWORD", ""),
        JWT_SECRET=os.getenv("JWT_SECRET", "change-this-secret"),  # override in .env
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000"),
        PORT=_int("PORT", 3001),
    )
