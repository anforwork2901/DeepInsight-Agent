import argparse
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.config import get_settings
from app.graph import build_graph
from app.services.database import get_database
from app.services.pdf_exporter import export_markdown_placeholder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeepInsight research agent.")
    parser.add_argument("topic", help="Research topic to investigate.")
    parser.add_argument("--depth", choices=["quick", "deep"], default="quick")
    parser.add_argument("--language", choices=["en", "vi"], default="en", help="Report language.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    thread_id = str(uuid4())
    graph = build_graph()
    result = graph.invoke({"topic": args.topic, "depth": args.depth, "report_language": args.language})

    report = result["final_report"]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = export_markdown_placeholder(report, Path("outputs") / f"report-{timestamp}.md")

    database = get_database(settings)
    if database:
        run_id = database.save_completed_run(thread_id=thread_id, state=result, output_path=str(output_path))
        print(f"Saved MySQL run: {run_id}")

    print(report)
    print(f"\nSaved report: {output_path}")


if __name__ == "__main__":
    main()
