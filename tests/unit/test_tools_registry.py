from config.settings import Settings


def test_create_tools_returns_tavily_tool(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    from tools.registry import create_tools

    settings = Settings(_env_file=None)
    tools = create_tools(settings)

    assert len(tools) == 1
    assert tools[0].name == "tavily_search"
