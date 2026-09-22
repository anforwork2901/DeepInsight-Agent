from app.config import Settings
from app.services.database import get_database


def test_database_disabled_by_default():
    settings = Settings(mysql_enabled=False)

    assert get_database(settings) is None


def test_database_enabled_returns_client():
    settings = Settings(mysql_enabled=True, mysql_password="secret")

    assert get_database(settings) is not None
