from langchain_tavily import TavilySearch

from config.settings import Settings


def create_tavily_search_tool(settings: Settings) -> TavilySearch:
    if not settings.tavily_api_key:
        raise ValueError("Missing API key for Tavily search: TAVILY_API_KEY")

    return TavilySearch(
        api_key=settings.tavily_api_key,
        max_results=5,
        topic="general",
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
        include_images=False,
    )
