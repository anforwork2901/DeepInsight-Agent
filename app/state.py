from typing import Literal, TypedDict


class ResearchSource(TypedDict, total=False):
    title: str
    url: str
    snippet: str
    score: float


class ResearchFinding(TypedDict):
    section: str
    summary: str
    sources: list[ResearchSource]


class CritiqueResult(TypedDict):
    passed: bool
    notes: list[str]
    follow_up_queries: list[str]


class AgentState(TypedDict, total=False):
    topic: str
    depth: Literal["quick", "deep"]
    report_language: Literal["en", "vi"]
    outline: list[str]
    human_feedback: str
    research_data: list[ResearchFinding]
    critique_notes: list[str]
    follow_up_queries: list[str]
    iteration_count: int
    final_report: str
