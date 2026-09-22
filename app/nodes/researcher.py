from app.config import get_settings
from app.services.search import get_search_client
from app.state import AgentState, ResearchFinding, ResearchSource


def researcher_node(state: AgentState) -> AgentState:
    settings = get_settings()
    search_client = get_search_client(settings)
    topic = state["topic"]
    language = state.get("report_language", "en")
    outline = state.get("outline", [])
    follow_ups = state.get("follow_up_queries", [])
    sections = outline[:3] if not follow_ups else follow_ups

    findings: list[ResearchFinding] = list(state.get("research_data", []))
    for section in sections:
        query = f"{topic} {section}"
        sources = search_client.search(query, max_results=settings.tavily_max_results)
        summary = _summarize_search_results(section=section, sources=sources, language=language)
        findings.append(
            {
                "section": section,
                "summary": summary,
                "sources": sources,
            }
        )

    return {"research_data": findings, "follow_up_queries": []}


def _summarize_search_results(section: str, sources: list[ResearchSource], language: str = "en") -> str:
    if not sources:
        if language == "vi":
            return f"Không tìm thấy nguồn web cho mục '{section}'."
        return f"No web sources found for '{section}'."

    snippets = [
        source.get("snippet", "").strip()
        for source in sources[:3]
        if source.get("snippet", "").strip()
    ]
    if not snippets:
        if language == "vi":
            return f"Tìm thấy {len(sources)} nguồn cho mục '{section}', nhưng các nguồn này chưa có đoạn trích hữu ích."
        return f"Found {len(sources)} source(s) for '{section}', but they did not include useful snippets."

    joined = " ".join(snippets)
    if language == "vi":
        return f"Bằng chứng tìm kiếm cho mục '{section}': {joined[:900]}"
    return f"Search evidence for '{section}': {joined[:900]}"
