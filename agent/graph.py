from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph

from config.settings import Settings
from services.llm_factory import create_chat_model
from agent.state import ScoutingState
from agent.prompts import SYSTEM_PROMPT


def build_graph(settings: Settings):
    llm = create_chat_model(settings)

    def agent_node(state: ScoutingState):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = llm.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(ScoutingState)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", END)

    return graph.compile()
