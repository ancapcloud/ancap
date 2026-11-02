import pytest

from app.config import Settings
from pathlib import Path


@pytest.fixture(autouse=True)
def _settings_ignore_local_dotenv(monkeypatch):
    """Keep these unit tests independent of a developer's local .env file."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)


def test_platform_admin_allowlists_have_no_default_account():
    assert Settings.model_fields["platform_admin_user_ids"].default == ""
    assert Settings.model_fields["platform_admin_emails"].default == ""


def test_prod_compose_has_no_default_personal_admin_email():
    compose = Path(__file__).resolve().parents[1] / "docker-compose.prod.yml"
    text = compose.read_text(encoding="utf-8")
    assert "dragon.cat.trx@gmail.com" not in text


def test_settings_parses_platform_admin_user_ids_from_csv():
    settings = Settings(platform_admin_user_ids="  user-1, user-2 ,, user-3  ")
    assert settings.platform_admin_user_ids_allowlist == ("user-1", "user-2", "user-3")


def test_settings_keeps_raw_platform_admin_user_ids_string_for_env_loading():
    settings = Settings(platform_admin_user_ids=" user-1 , , user-2 ")
    assert settings.platform_admin_user_ids == " user-1 , , user-2 "
    assert settings.platform_admin_user_ids_allowlist == ("user-1", "user-2")


def test_settings_parses_empty_platform_admin_user_ids_as_empty_tuple():
    settings = Settings(platform_admin_user_ids="   ,  , ")
    assert settings.platform_admin_user_ids_allowlist == ()


def test_settings_requires_secret_key_cursor_secret_and_cron_secret_in_production():
    valid_secret = "7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890"
    valid_cursor = "9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd"
    valid_cron = "3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987"

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] SECRET_KEY is not set"):
        Settings(environment="production", secret_key="", cursor_secret=valid_cursor, cron_secret=valid_cron)

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] CURSOR_SECRET is not set"):
        Settings(environment="production", secret_key=valid_secret, cursor_secret="", cron_secret=valid_cron)

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] CRON_SECRET is not set"):
        Settings(environment="production", secret_key=valid_secret, cursor_secret=valid_cursor, cron_secret="")


def test_settings_rejects_placeholder_production_secrets():
    valid_secret = "7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890"
    valid_cursor = "9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd"
    valid_cron = "3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987"

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] SECRET_KEY has an insecure placeholder"):
        Settings(environment="production", secret_key="change-me-in-production", cursor_secret=valid_cursor, cron_secret=valid_cron)

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] CURSOR_SECRET has an insecure placeholder"):
        Settings(environment="production", secret_key=valid_secret, cursor_secret="dev-secret-cursor", cron_secret=valid_cron)

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] CRON_SECRET has an insecure placeholder"):
        Settings(environment="production", secret_key=valid_secret, cursor_secret=valid_cursor, cron_secret="example-cron-secret")


def test_settings_rejects_insecure_default_or_invalid_database_url_in_production():
    valid_secret = "7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890"
    valid_cursor = "9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd"
    valid_cron = "3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987"

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL is not set"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL is not a valid absolute URI"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="not-a-uri",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL is not a valid absolute URI"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://ancap:real-db-password@/ancap?ghost=postgres",
        )

    bundled_default_user = "".join(("post", "gres"))
    bundled_default_password = "".join(("post", "gres"))

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL still uses the insecure bundled database default credentials"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url=f"postgresql+asyncpg://{bundled_default_user}:{bundled_default_password}@postgres:5432/ancap",
        )


def test_settings_rejects_placeholder_or_default_database_passwords_in_production():
    valid_secret = "7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890"
    valid_cursor = "9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd"
    valid_cron = "3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987"

    bundled_default_password = "".join(("post", "gres"))

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL still uses the insecure default database password"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url=f"postgresql+asyncpg://ancap:{bundled_default_password}@db.example.com:5432/ancap",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL uses a placeholder-like database password"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://ancap:change-me-db-password@db.example.com:5432/ancap",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL targets the bundled postgres service but does not include a password"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://ancap@postgres:5432/ancap",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL username does not match POSTGRES_USER for the bundled postgres service"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://ancap:real-db-password@postgres:5432/ancap",
            postgres_password="real-db-password",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL database name does not match POSTGRES_DB for the bundled postgres service"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://postgres:real-db-password@postgres:5432/not-ancap",
            postgres_password="real-db-password",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] POSTGRES_PASSWORD is not set"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://postgres:real-db-password@postgres:5432/ancap",
            postgres_password="",
        )

    bundled_default_password = "".join(("post", "gres"))

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] POSTGRES_PASSWORD still uses the insecure default value"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://postgres:real-db-password@postgres:5432/ancap",
            postgres_password=bundled_default_password,
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] POSTGRES_PASSWORD uses a placeholder-like value"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://postgres:real-db-password@postgres:5432/ancap",
            postgres_password="change-me-db-password",
        )

    with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL password does not match POSTGRES_PASSWORD for the bundled postgres service"):
        Settings(
            environment="production",
            secret_key=valid_secret,
            cursor_secret=valid_cursor,
            cron_secret=valid_cron,
            database_url="postgresql+asyncpg://postgres:real-db-password@postgres:5432/ancap",
            postgres_password="different-db-password",
        )


def test_settings_accepts_urlencoded_bundled_postgres_password_when_it_matches_postgres_password():
    settings = Settings(
        environment="production",
        secret_key="7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890",
        cursor_secret="9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd",
        cron_secret="3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987",
        database_url="postgresql+asyncpg://postgres:p%40ss%3Aword@postgres:5432/ancap",
        postgres_password="p@ss:word",
    )

    assert settings.database_url == "postgresql+asyncpg://postgres:p%40ss%3Aword@postgres:5432/ancap"
    assert settings.postgres_password == "p@ss:word"


def test_settings_enforces_bundled_postgres_guards_for_socket_style_host_query():
    valid_secret = "7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890"
    valid_cursor = "9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd"
    valid_cron = "3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987"

    for socket_host in ("postgres", "%70ostgres"):
        with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL targets the bundled postgres service but does not include a password"):
            Settings(
                environment="production",
                secret_key=valid_secret,
                cursor_secret=valid_cursor,
                cron_secret=valid_cron,
                database_url=f"postgresql+asyncpg://postgres@/ancap?host={socket_host}",
                postgres_password="real-db-password",
            )

        with pytest.raises(ValueError, match=r"\[PRODUCTION\] DATABASE_URL password does not match POSTGRES_PASSWORD for the bundled postgres service"):
            Settings(
                environment="production",
                secret_key=valid_secret,
                cursor_secret=valid_cursor,
                cron_secret=valid_cron,
                database_url=f"postgresql+asyncpg://postgres:real-db-password@/ancap?host={socket_host}",
                postgres_password="different-db-password",
            )


def test_settings_accepts_urlencoded_bundled_postgres_password_for_socket_style_host_query():
    for socket_host in ("postgres", "%70ostgres"):
        settings = Settings(
            environment="production",
            secret_key="7b6e8a4c1d2f3a5b7c9e0f1234567890abcdef1234567890abcdef1234567890",
            cursor_secret="9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcd",
            cron_secret="3c2b1a0f9e8d7c6b5a43210fedcba9876543210fedcba9876543210fedcba987",
            database_url=f"postgresql+asyncpg://postgres:p%40ss%3Aword@/ancap?host={socket_host}",
            postgres_password="p@ss:word",
        )

        assert settings.database_url == f"postgresql+asyncpg://postgres:p%40ss%3Aword@/ancap?host={socket_host}"
        assert settings.postgres_password == "p@ss:word"
