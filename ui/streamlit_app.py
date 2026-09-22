from datetime import datetime
from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.graph import build_research_graph
from app.nodes.planner import planner_node
from app.services.database import get_database
from app.services.pdf_exporter import export_markdown_placeholder
from app.state import AgentState


st.set_page_config(page_title="DeepInsight Agent", layout="wide")


def init_session_state() -> None:
    defaults = {
        "thread_id": None,
        "run_id": None,
        "agent_state": None,
        "report": None,
        "output_path": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_run() -> None:
    st.session_state.thread_id = None
    st.session_state.run_id = None
    st.session_state.agent_state = None
    st.session_state.report = None
    st.session_state.output_path = None


def generate_outline(topic: str, depth: str, report_language: str, database) -> None:
    thread_id = str(uuid4())
    state: AgentState = {"topic": topic, "depth": depth, "report_language": report_language}
    state.update(planner_node(state))

    run_id = None
    if database:
        run_id = database.save_awaiting_human_run(thread_id=thread_id, state=state)

    st.session_state.thread_id = thread_id
    st.session_state.run_id = run_id
    st.session_state.agent_state = state
    st.session_state.report = None
    st.session_state.output_path = None


def apply_feedback(feedback: str, database) -> None:
    state = st.session_state.agent_state
    if not state:
        return

    state["human_feedback"] = feedback
    state.update(planner_node(state))
    st.session_state.agent_state = state

    if database and st.session_state.thread_id:
        st.session_state.run_id = database.save_awaiting_human_run(
            thread_id=st.session_state.thread_id,
            state=state,
        )


def approve_and_research(database) -> None:
    state = st.session_state.agent_state
    thread_id = st.session_state.thread_id
    if not state or not thread_id:
        return

    if database:
        database.mark_run_status(
            thread_id=thread_id,
            status="running",
            human_feedback=state.get("human_feedback"),
        )

    graph = build_research_graph()
    result = graph.invoke(state)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = export_markdown_placeholder(
        result["final_report"],
        Path("outputs") / f"ui-hitl-report-{timestamp}.md",
    )

    if database:
        st.session_state.run_id = database.save_completed_run(
            thread_id=thread_id,
            state=result,
            output_path=str(output_path),
        )

    st.session_state.agent_state = result
    st.session_state.report = result["final_report"]
    st.session_state.output_path = str(output_path)


def render_history(database) -> None:
    st.subheader("Recent Runs")
    if not database:
        st.caption("MySQL is disabled.")
        return

    try:
        counts = database.get_run_summary_counts()
        c1, c2, c3 = st.columns(3)
        c1.metric("Runs", counts["runs"])
        c2.metric("Findings", counts["findings"])
        c3.metric("Sources", counts["sources"])

        rows = database.list_recent_runs(limit=8)
    except Exception as exc:
        st.error(f"MySQL error: {exc}")
        return

    if not rows:
        st.caption("No saved runs yet.")
        return

    for row in rows:
        label = f"#{row['id']} · {row['status']} · {row['topic']}"
        with st.expander(label):
            st.write(f"Depth: `{row['depth']}`")
            st.write(f"Thread: `{row['thread_id']}`")
            if row.get("output_path"):
                st.write(f"Output: `{row['output_path']}`")
            st.write(f"Updated: `{row['updated_at']}`")


init_session_state()
settings = get_settings()
database = get_database(settings)

st.title("DeepInsight Agent")

with st.sidebar:
    st.subheader("Research Setup")
    topic = st.text_input("Topic", placeholder="AI adoption trends in Vietnamese SMEs")
    depth = st.segmented_control("Depth", ["quick", "deep"], default="quick")
    language_label = st.segmented_control("Language", ["English", "Tiếng Việt"], default="English")
    report_language = "vi" if language_label == "Tiếng Việt" else "en"
    generate = st.button("Generate Outline", type="primary", disabled=not topic)
    st.button("New Run", on_click=reset_run)

    st.divider()
    render_history(database)

if generate and topic:
    with st.spinner("Planning outline..."):
        try:
            generate_outline(topic=topic, depth=depth, report_language=report_language, database=database)
        except Exception as exc:
            st.error(f"Failed to generate outline: {exc}")

left, right = st.columns([0.9, 1.1], gap="large")

with left:
    st.subheader("Outline Review")
    state = st.session_state.agent_state
    if not state:
        st.info("Create an outline to begin.")
    else:
        if st.session_state.run_id:
            st.caption(f"MySQL run #{st.session_state.run_id}")

        for index, section in enumerate(state.get("outline", []), start=1):
            st.write(f"{index}. {section}")

        feedback = st.text_area("Feedback", placeholder="Focus more on Vietnam SMEs and concrete adoption metrics.")
        feedback_col, approve_col = st.columns(2)
        with feedback_col:
            if st.button("Apply Feedback", disabled=not feedback.strip()):
                with st.spinner("Updating outline..."):
                    try:
                        apply_feedback(feedback=feedback.strip(), database=database)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to apply feedback: {exc}")
        with approve_col:
            if st.button("Approve & Research", type="primary"):
                with st.spinner("Researching sources and writing report..."):
                    try:
                        approve_and_research(database=database)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Research failed: {exc}")

with right:
    st.subheader("Report")
    if st.session_state.report:
        st.markdown(st.session_state.report)
        if st.session_state.output_path:
            st.caption(f"Saved to `{st.session_state.output_path}`")
        st.download_button(
            "Download Markdown",
            data=st.session_state.report,
            file_name="deepinsight-report.md",
            mime="text/markdown",
        )
    else:
        st.info("Approve an outline to generate the report.")
