from config.settings import Settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from agent.prompts import SYSTEM_PROMPT


class FakeLLM:
    def __init__(self):
        self.received_messages = None

    def invoke(self, messages):
        self.received_messages = messages
        return AIMessage(content="Respuesta fake")


def test_build_graph_returns_invokable_graph(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from agent.graph import build_graph

    settings = Settings(_env_file=None)
    graph = build_graph(settings)

    assert hasattr(graph, "invoke")


def test_graph_invokes_llm_and_appends_ai_message(monkeypatch):
    fake_llm = FakeLLM()

    monkeypatch.setattr(
        "agent.graph.create_chat_model",
        lambda settings: fake_llm,
    )

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

    from agent.graph import build_graph

    settings = object()
    graph = build_graph(settings)

    graph.invoke({"messages": [HumanMessage(content="Busca delanteros sub-21")]})

    assert fake_llm.received_messages == [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="Busca delanteros sub-21"),
    ]
