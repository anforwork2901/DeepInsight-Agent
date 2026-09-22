import argparse
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.config import get_settings
from app.graph import build_research_graph
from app.nodes.planner import planner_node
from app.services.database import get_database
from app.services.pdf_exporter import export_markdown_placeholder
from app.state import AgentState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DeepInsight with human outline approval.")
    parser.add_argument("topic", help="Research topic to investigate.")
    parser.add_argument("--depth", choices=["quick", "deep"], default="quick")
    parser.add_argument("--language", choices=["en", "vi"], default="en", help="Report language.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    database = get_database(settings)
    thread_id = str(uuid4())

    state: AgentState = {"topic": args.topic, "depth": args.depth, "report_language": args.language}
    state.update(planner_node(state))

    if database:
        run_id = database.save_awaiting_human_run(thread_id=thread_id, state=state)
        print(f"Saved awaiting-human MySQL run: {run_id}")

    print("\nProposed outline:")
    for index, section in enumerate(state.get("outline", []), start=1):
        print(f"{index}. {section}")

    approval = input("\nApprove this outline? [y/N]: ").strip().lower()
    if approval not in {"y", "yes"}:
        feedback = input("What should the planner adjust? ").strip()
        if feedback:
            state["human_feedback"] = feedback
            state.update(planner_node(state))
            if database:
                database.save_awaiting_human_run(thread_id=thread_id, state=state)

            print("\nUpdated outline:")
            for index, section in enumerate(state.get("outline", []), start=1):
                print(f"{index}. {section}")

            second_approval = input("\nApprove updated outline? [y/N]: ").strip().lower()
            if second_approval not in {"y", "yes"}:
                if database:
                    database.mark_run_status(thread_id=thread_id, status="planned", human_feedback=feedback)
                print("Stopped before research. Outline remains saved for review.")
                return
        else:
            if database:
                database.mark_run_status(thread_id=thread_id, status="planned")
            print("Stopped before research. Outline remains saved for review.")
            return

    if database:
        database.mark_run_status(
            thread_id=thread_id,
            status="running",
            human_feedback=state.get("human_feedback"),
        )

    graph = build_research_graph()
    result = graph.invoke(state)

    report = result["final_report"]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = export_markdown_placeholder(report, Path("outputs") / f"hitl-report-{timestamp}.md")

    if database:
        run_id = database.save_completed_run(thread_id=thread_id, state=result, output_path=str(output_path))
        print(f"Saved completed MySQL run: {run_id}")

    print("\nFinal report:\n")
    print(report)
    print(f"\nSaved report: {output_path}")


if __name__ == "__main__":
    main()
