from config.settings import Settings
from tools.tavily_search import create_tavily_search_tool


def create_tools(settings: Settings):
    return [create_tavily_search_tool(settings)]
