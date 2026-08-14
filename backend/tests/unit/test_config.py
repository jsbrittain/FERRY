import pytest

from app.core.config import Settings

LONG_KEY = "a" * 32


def test_settings_loads_with_minimal_env():
    s = Settings(
        _env_file=None,
        postgres_password="test-pw",
        postgres_host="localhost",
        postgres_db="ferry",
        redis_password="test-redis",
        secret_key=LONG_KEY,
    )
    assert s.postgres_host == "localhost"
    assert s.postgres_port == 5432
    assert s.postgres_db == "ferry"
    assert str(s.public_url) == "https://localhost"
    assert s.admin_email == "admin@ferry.local"


def test_settings_database_url_property():
    s = Settings(
        postgres_user="custom",
        postgres_password="pw",
        postgres_host="db.example.com",
        postgres_port=15432,
        postgres_db="custom_db",
        redis_password="rpw",
        secret_key=LONG_KEY,
    )
    assert s.database_url == "postgresql://custom:pw@db.example.com:15432/custom_db"


def test_settings_env_file_config():
    s = Settings(
        postgres_password="pw",
        redis_password="rpw",
        secret_key=LONG_KEY,
    )
    assert s.model_config.get("env_file") == ".env"


def test_settings_short_secret_key_rejected():
    with pytest.raises(ValueError, match="at least 32 characters"):
        Settings(
            _env_file=None,
            postgres_password="pw",
            redis_password="rpw",
            secret_key="tooshort",
        )
