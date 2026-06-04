import pytest
from config.settings import Settings


def test_creates_tavily_search_tool(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    from tools.tavily_search import create_tavily_search_tool

    settings = Settings(_env_file=None)
    tool = create_tavily_search_tool(settings)

    assert tool.max_results == 5


def test_requires_tavily_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    from tools.tavily_search import create_tavily_search_tool

    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        create_tavily_search_tool(settings)
