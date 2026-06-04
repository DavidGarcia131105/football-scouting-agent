import sys

from langchain_core.messages import HumanMessage

from agent.graph import build_graph
from config.settings import Settings


def run_cli(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print('Usage: python main.py "tu pregunta"')
        return 1

    question = " ".join(argv)
    settings = Settings()
    graph = build_graph(settings)
    result = graph.invoke({"messages": [HumanMessage(content=question)]})
    final_message = result["messages"][-1]

    print(final_message.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
