from langchain_core.messages import AIMessage, HumanMessage


class FakeGraph:
    def __init__(self):
        self.received_state = None

    def invoke(self, state):
        self.received_state = state
        return {"messages": [AIMessage(content="Respuesta final fake")]}


def test_run_cli_without_question_print_usage(capsys):
    from main import run_cli

    exit_code = run_cli([])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert 'Usage: python main.py "tu pregunta"' in captured.out


def test_run_cli_invokes_graph_and_prints_last_ai_message(monkeypatch, capsys):
    fake_graph = FakeGraph()

    monkeypatch.setattr("main.Settings", lambda: object())
    monkeypatch.setattr("main.build_graph", lambda settings: fake_graph)

    from main import run_cli

    exit_code = run_cli(["Analiza a Lamine Yamal"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_graph.received_state == {
        "messages": [HumanMessage(content="Analiza a Lamine Yamal")]
    }
    assert "Respuesta final fake" in captured.out
