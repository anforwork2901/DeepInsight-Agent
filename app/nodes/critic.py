from app.config import get_settings
from app.services.llm import get_llm
from app.state import AgentState


def critic_node(state: AgentState) -> AgentState:
    settings = get_settings()
    llm = get_llm(settings)
    iteration_count = state.get("iteration_count", 0) + 1
    passed, notes, follow_up_queries = llm.critique(
        topic=state["topic"],
        outline=state.get("outline", []),
        research_data=state.get("research_data", []),
        iteration_count=iteration_count,
        language=state.get("report_language", "en"),
    )

    return {
        "critique_notes": notes,
        "follow_up_queries": follow_up_queries,
        "iteration_count": iteration_count,
        "_critique_passed": passed,
    }


def route_after_critic(state: AgentState) -> str:
    passed = bool(state.get("_critique_passed"))
    if passed or state.get("iteration_count", 0) >= 3:
        return "writer"
    return "researcher"
