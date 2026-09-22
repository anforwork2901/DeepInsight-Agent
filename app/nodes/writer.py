from app.config import get_settings
from app.services.llm import get_llm
from app.state import AgentState


def writer_node(state: AgentState) -> AgentState:
    settings = get_settings()
    llm = get_llm(settings)
    report = llm.write_report(
        topic=state["topic"],
        outline=state.get("outline", []),
        research_data=state.get("research_data", []),
        critique_notes=state.get("critique_notes", []),
        language=state.get("report_language", "en"),
    )
    return {"final_report": report}
