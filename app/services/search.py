from app.config import Settings
from app.state import ResearchSource


class DemoSearchClient:
    """Deterministic search substitute used before Tavily is configured."""

    def search(self, query: str, max_results: int = 5) -> list[ResearchSource]:
        return [
            {
                "title": f"Demo source for {query}",
                "url": "https://example.com/research-placeholder",
                "snippet": f"Placeholder evidence related to: {query}. Replace with Tavily results in Phase 2.",
                "score": 0.75,
            }
        ][:max_results]


class TavilySearchClient:
    def __init__(self, api_key: str):
        from tavily import TavilyClient

        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> list[ResearchSource]:
        response = self.client.search(
            query=query,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
        results = response.get("results", []) if isinstance(response, dict) else []
        return [
            {
                "title": result.get("title", "Untitled"),
                "url": result.get("url", ""),
                "snippet": result.get("content", ""),
                "score": float(result.get("score", 0.0) or 0.0),
            }
            for result in results
        ]


def get_search_client(settings: Settings) -> DemoSearchClient | TavilySearchClient:
    if settings.tavily_api_key:
        return TavilySearchClient(settings.tavily_api_key)
    return DemoSearchClient()
