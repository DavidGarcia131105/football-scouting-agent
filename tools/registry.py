from config.settings import Settings
from tools.fbref_stats import create_fbref_stats_tool
from tools.tavily_search import create_tavily_search_tool


def create_tools(settings: Settings):
    return [
        create_tavily_search_tool(settings),
        create_fbref_stats_tool(settings),
    ]
