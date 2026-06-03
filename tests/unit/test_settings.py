import pytest
from pydantic import ValidationError


def test_loads_valid_deepseek_settings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from config.settings import Settings

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "deepseek"
    assert settings.llm_model == "deepseek-chat"


def test_rejects_unknown_llm_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_rejects_model_not_supported_by_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_requires_api_key_for_active_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    from config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
