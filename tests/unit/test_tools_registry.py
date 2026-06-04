from config.settings import Settings


def test_create_tools_returns_available_tools(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    from tools.registry import create_tools

    settings = Settings(_env_file=None)
    tools = create_tools(settings)
    tool_names = [tool.name for tool in tools]

    assert "tavily_search" in tool_names
    assert "fbref_stats" in tool_names
