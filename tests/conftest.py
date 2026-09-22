import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def use_demo_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "demo")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
