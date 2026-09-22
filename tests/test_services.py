import pytest

from app.config import Settings
from app.services.llm import get_llm


def test_openai_provider_requires_api_key():
    settings = Settings(llm_provider="openai", openai_api_key=None)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_llm(settings)


def test_gemini_provider_requires_api_key():
    settings = Settings(llm_provider="gemini", google_api_key=None)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        get_llm(settings)
