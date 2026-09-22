import json
from contextlib import contextmanager
from typing import Iterator

from app.config import Settings
from app.state import AgentState, ResearchFinding


class MySQLDatabase:
    def __init__(self, settings: Settings):
        self.settings = settings

    @contextmanager
    def connection(self) -> Iterator:
        import mysql.connector

        conn = mysql.connector.connect(
            host=self.settings.mysql_host,
            port=self.settings.mysql_port,
            user=self.settings.mysql_user,
            password=self.settings.mysql_password or "",
            database=self.settings.mysql_database,
        )
        try:
            yield conn
        finally:
            conn.close()

    def save_awaiting_human_run(self, thread_id: str, state: AgentState) -> int:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO research_runs (
                    thread_id,
                    topic,
                    depth,
                    status,
                    outline_json,
                    human_feedback
                )
                VALUES (%s, %s, %s, 'awaiting_human', %s, %s)
                ON DUPLICATE KEY UPDATE
                    topic = VALUES(topic),
                    depth = VALUES(depth),
                    status = 'awaiting_human',
                    outline_json = VALUES(outline_json),
                    human_feedback = VALUES(human_feedback)
                """,
                (
                    thread_id,
                    state["topic"],
                    state.get("depth", "quick"),
                    json.dumps(state.get("outline", []), ensure_ascii=False),
                    state.get("human_feedback"),
                ),
            )
            conn.commit()
            cursor.execute("SELECT id FROM research_runs WHERE thread_id = %s", (thread_id,))
            return int(cursor.fetchone()[0])

    def mark_run_status(self, thread_id: str, status: str, human_feedback: str | None = None) -> None:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE research_runs
                SET status = %s,
                    human_feedback = COALESCE(%s, human_feedback)
                WHERE thread_id = %s
                """,
                (status, human_feedback, thread_id),
            )
            conn.commit()

    def list_recent_runs(self, limit: int = 10) -> list[dict]:
        with self.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    thread_id,
                    topic,
                    depth,
                    status,
                    output_path,
                    created_at,
                    updated_at,
                    completed_at
                FROM research_runs
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return list(cursor.fetchall())

    def get_run_summary_counts(self) -> dict[str, int]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM research_runs")
            runs = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM research_findings")
            findings = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM research_sources")
            sources = int(cursor.fetchone()[0])
            return {"runs": runs, "findings": findings, "sources": sources}

    def save_completed_run(self, thread_id: str, state: AgentState, output_path: str) -> int:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO research_runs (
                    thread_id,
                    topic,
                    depth,
                    status,
                    outline_json,
                    human_feedback,
                    critique_notes_json,
                    final_report,
                    output_path,
                    completed_at
                )
                VALUES (%s, %s, %s, 'completed', %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                    topic = VALUES(topic),
                    depth = VALUES(depth),
                    status = 'completed',
                    outline_json = VALUES(outline_json),
                    human_feedback = VALUES(human_feedback),
                    critique_notes_json = VALUES(critique_notes_json),
                    final_report = VALUES(final_report),
                    output_path = VALUES(output_path),
                    completed_at = CURRENT_TIMESTAMP
                """,
                (
                    thread_id,
                    state["topic"],
                    state.get("depth", "quick"),
                    json.dumps(state.get("outline", []), ensure_ascii=False),
                    state.get("human_feedback"),
                    json.dumps(state.get("critique_notes", []), ensure_ascii=False),
                    state.get("final_report", ""),
                    output_path,
                ),
            )
            cursor.execute("SELECT id FROM research_runs WHERE thread_id = %s", (thread_id,))
            run_id = int(cursor.fetchone()[0])
            cursor.execute("DELETE FROM research_findings WHERE run_id = %s", (run_id,))
            self._insert_findings(cursor, run_id, state.get("research_data", []))
            conn.commit()
            return run_id

    def _insert_findings(self, cursor, run_id: int, findings: list[ResearchFinding]) -> None:
        for finding in findings:
            cursor.execute(
                """
                INSERT INTO research_findings (run_id, section_title, summary)
                VALUES (%s, %s, %s)
                """,
                (run_id, finding["section"], finding["summary"]),
            )
            finding_id = cursor.lastrowid
            for source in finding.get("sources", []):
                cursor.execute(
                    """
                    INSERT INTO research_sources (finding_id, title, url, snippet, score)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        finding_id,
                        source.get("title", "Untitled"),
                        source.get("url", ""),
                        source.get("snippet", ""),
                        source.get("score"),
                    ),
                )


def get_database(settings: Settings) -> MySQLDatabase | None:
    if not settings.mysql_enabled:
        return None
    return MySQLDatabase(settings)
