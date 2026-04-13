import os
from dotenv import dotenv_values

# Load from .env file (as fallback)
fallback_env = dotenv_values(".env")


def get_env_var(key, fallback_dict=fallback_env):
    """Retrieves the value of an environment variable, falling back to a provided dictionary."""
    return os.environ.get(key, fallback_dict.get(key))


class Config:
    """Base configuration class."""

    # Attempt to construct the primary database URI
    try:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+mysqlconnector://{get_env_var('DB_USER')}:{get_env_var('DB_PASSWORD')}"
            f"@{get_env_var('DB_HOST')}:{int(get_env_var('DB_PORT'))}/{get_env_var('DB_NAME')}"
        )
    except (TypeError, ValueError):
        # Fallback to in-memory SQLite if any required variable is missing or invalid
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    SQLALCHEMY_TRACK_MODIFICATIONS = False