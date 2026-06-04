from config.settings import Settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from agent.prompts import SYSTEM_PROMPT


class FakeLLM:
    def __init__(self):
        self.received_messages = None
        self.bound_tools = None

    def bind_tools(self, tools):
        self.bound_tools = tools
        return self

    def invoke(self, messages):
        self.received_messages = messages
        return AIMessage(content="Respuesta fake")


def test_build_graph_returns_invokable_graph(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from agent.graph import build_graph

    monkeypatch.setattr("agent.graph.create_tools", lambda settings: [])

    settings = Settings(_env_file=None)
    graph = build_graph(settings)

    assert hasattr(graph, "invoke")


def test_graph_invokes_llm_and_appends_ai_message(monkeypatch):
    fake_llm = FakeLLM()

    monkeypatch.setattr(
        "agent.graph.create_chat_model",
        lambda settings: fake_llm,
    )
    monkeypatch.setattr("agent.graph.create_tools", lambda settings: [])

    from agent.graph import build_graph

    settings = object()
    graph = build_graph(settings)

    result = graph.invoke(
        {"messages": [HumanMessage(content="Analiza a Lamine Yamal")]}
    )

    assert fake_llm.received_messages == [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="Analiza a Lamine Yamal"),
    ]

    assert result["messages"][-1] == AIMessage(content="Respuesta fake")


def test_graph_injects_system_prompt_before_user_messages(monkeypatch):
    fake_llm = FakeLLM()

    monkeypatch.setattr("agent.graph.create_chat_model", lambda settings: fake_llm)
    monkeypatch.setattr("agent.graph.create_tools", lambda settings: [])

    from agent.graph import build_graph

    settings = object()
    graph = build_graph(settings)

    graph.invoke({"messages": [HumanMessage(content="Busca delanteros sub-21")]})

    assert fake_llm.received_messages == [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="Busca delanteros sub-21"),
    ]


def test_graph_binds_tools_to_llm(monkeypatch):
    fake_llm = FakeLLM()

    @tool
    def fake_search(query: str) -> str:
        """Fake search tool."""
        return f"fake result for {query}"

    fake_tools = [fake_search]

    monkeypatch.setattr("agent.graph.create_chat_model", lambda settings: fake_llm)
    monkeypatch.setattr("agent.graph.create_tools", lambda settings: fake_tools)

    from agent.graph import build_graph

    graph = build_graph(object())

    assert hasattr(graph, "invoke")
    assert fake_llm.bound_tools == fake_tools


def test_should_continue_routes_to_tools_when_last_message_has_tool_calls():
    from agent.graph import should_continue

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "tavily_search",
                "args": {"query": "Lamine Yamal últimas noticias"},
                "id": "call_1",
                "type": "tool_call",
            }
        ],
    )

    assert should_continue({"messages": [message]}) == "tools"


def test_should_continue_ends_when_last_message_has_no_tool_calls():
    from langgraph.graph import END
    from agent.graph import should_continue

    message = AIMessage(content="Respuesta final")

    assert should_continue({"messages": [message]}) == END
