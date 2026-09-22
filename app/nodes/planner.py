from app.config import get_settings
from app.services.llm import get_llm
from app.state import AgentState


def planner_node(state: AgentState) -> AgentState:
    settings = get_settings()
    llm = get_llm(settings)
    topic = state["topic"]
    depth = state.get("depth", "quick")
    language = state.get("report_language", "en")
    outline = llm.create_outline(topic=topic, depth=depth, language=language)

    if state.get("human_feedback"):
        if language == "vi":
            outline.append(f"Trọng tâm phản hồi của người dùng: {state['human_feedback']}")
        else:
            outline.append(f"Human feedback focus: {state['human_feedback']}")

    return {"outline": outline, "iteration_count": state.get("iteration_count", 0)}
