from typing import Protocol

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import Settings
from app.state import ResearchFinding, ResearchSource


class OutlineResponse(BaseModel):
    sections: list[str] = Field(description="A concise, ordered research outline.")


class SourceSummaryResponse(BaseModel):
    summary: str = Field(description="A source-grounded summary for one report section.")


class CritiqueResponse(BaseModel):
    passed: bool = Field(description="Whether the evidence is strong enough to write the report.")
    notes: list[str] = Field(description="Specific critique notes about evidence quality.")
    follow_up_queries: list[str] = Field(description="Targeted web search queries if more research is needed.")


class ReportResponse(BaseModel):
    markdown: str = Field(description="The final professional research report in Markdown.")


class ResearchLLM(Protocol):
    def create_outline(self, topic: str, depth: str, language: str = "en") -> list[str]:
        ...

    def summarize_sources(self, topic: str, section: str, sources: list[ResearchSource], language: str = "en") -> str:
        ...

    def critique(
        self,
        topic: str,
        outline: list[str],
        research_data: list[ResearchFinding],
        iteration_count: int,
        language: str = "en",
    ) -> tuple[bool, list[str], list[str]]:
        ...

    def write_report(
        self,
        topic: str,
        outline: list[str],
        research_data: list[ResearchFinding],
        critique_notes: list[str],
        language: str = "en",
    ) -> str:
        ...


class DemoLLM:
    """Deterministic LLM substitute for local graph development."""

    def create_outline(self, topic: str, depth: str, language: str = "en") -> list[str]:
        if language == "vi":
            base_outline = [
                "Tóm tắt điều hành và phạm vi nghiên cứu",
                "Bối cảnh thị trường và các xu hướng chính",
                "Bằng chứng, số liệu và ví dụ đáng chú ý",
                "Rủi ro, hạn chế và câu hỏi còn bỏ ngỏ",
                "Khuyến nghị hành động",
            ]
            if depth == "deep":
                return base_outline + ["Phân tích kịch bản và định hướng nghiên cứu tiếp theo"]
            return base_outline

        base_outline = [
            "Executive summary and research scope",
            "Market context and key trends",
            "Evidence, metrics, and notable examples",
            "Risks, limitations, and open questions",
            "Actionable recommendations",
        ]
        if depth == "deep":
            return base_outline + ["Scenario analysis and next-step research agenda"]
        return base_outline

    def summarize_sources(self, topic: str, section: str, sources: list[ResearchSource], language: str = "en") -> str:
        source_count = len(sources)
        if language == "vi":
            return f"Đã thu thập bằng chứng sơ bộ cho mục '{section}' từ {source_count} nguồn."
        return f"Collected preliminary evidence for '{section}' from {source_count} source(s)."

    def critique(
        self,
        topic: str,
        outline: list[str],
        research_data: list[ResearchFinding],
        iteration_count: int,
        language: str = "en",
    ) -> tuple[bool, list[str], list[str]]:
        findings_count = len(research_data)
        if findings_count >= 3 or iteration_count >= 1:
            if language == "vi":
                return True, ["Bản nháp có đủ bằng chứng ban đầu để tạo báo cáo đầu tiên."], []
            return True, ["The draft has enough starter evidence for a first report."], []
        if language == "vi":
            return False, ["Cần bổ sung bằng chứng cụ thể và nguồn trích dẫn rõ ràng hơn."], [f"{topic} số liệu nghiên cứu tình huống"]
        return False, ["Add more concrete evidence and cited sources."], [f"{topic} statistics case studies"]

    def write_report(
        self,
        topic: str,
        outline: list[str],
        research_data: list[ResearchFinding],
        critique_notes: list[str],
        language: str = "en",
    ) -> str:
        summaries_by_section = {
            finding["section"]: _format_demo_finding_for_report(finding)
            for finding in research_data
        }
        missing_text = "Cần nghiên cứu thêm." if language == "vi" else "Further research needed."
        sections = "\n\n".join(
            f"## {heading}\n\n{summaries_by_section.get(heading, missing_text)}"
            for heading in outline
        )
        notes = "\n".join(f"- {note}" for note in critique_notes) or "- No critique notes."
        sources = _format_all_sources_for_report(research_data)
        if language == "vi":
            notes = "\n".join(f"- {note}" for note in critique_notes) or "- Không có ghi chú phản biện."
            return f"# {topic}\n\n{sections}\n\n## Nguồn tham khảo\n\n{sources}\n\n## Ghi chú chất lượng\n\n{notes}\n"
        return f"# {topic}\n\n{sections}\n\n## Sources\n\n{sources}\n\n## Quality Notes\n\n{notes}\n"


class LangChainResearchLLM:
    """LangChain-backed implementation for real LLM providers."""

    def __init__(self, models: list[BaseChatModel]):
        self.models = models

    def create_outline(self, topic: str, depth: str, language: str = "en") -> list[str]:
        output_language = _language_name(language)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a senior research planner. Create a practical outline for a web-grounded research report. "
                    "Return the outline in {output_language}.",
                ),
                (
                    "human",
                    "Topic: {topic}\nDepth: {depth}\nLanguage: {output_language}\n"
                    "Return 5-7 clear section headings. Avoid generic filler.",
                ),
            ]
        )
        result = self._invoke_structured(
            prompt=prompt,
            response_model=OutlineResponse,
            payload={"topic": topic, "depth": depth, "output_language": output_language},
        )
        return result.sections

    def summarize_sources(self, topic: str, section: str, sources: list[ResearchSource], language: str = "en") -> str:
        output_language = _language_name(language)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You summarize web search evidence. Stay grounded in the provided sources and do not invent facts. "
                    "Write in {output_language}.",
                ),
                (
                    "human",
                    "Topic: {topic}\nSection: {section}\nLanguage: {output_language}\nSources:\n{sources}\n\n"
                    "Write a concise evidence summary for this section. Mention uncertainty when sources are thin.",
                ),
            ]
        )
        result = self._invoke_structured(
            prompt=prompt,
            response_model=SourceSummaryResponse,
            payload={
                "topic": topic,
                "section": section,
                "output_language": output_language,
                "sources": _format_sources_for_prompt(sources),
            },
        )
        return result.summary

    def critique(
        self,
        topic: str,
        outline: list[str],
        research_data: list[ResearchFinding],
        iteration_count: int,
        language: str = "en",
    ) -> tuple[bool, list[str], list[str]]:
        output_language = _language_name(language)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a strict research critic. Check whether evidence is specific, relevant, and source-backed. "
                    "Write critique notes and follow-up queries in {output_language}.",
                ),
                (
                    "human",
                    "Topic: {topic}\nLanguage: {output_language}\nIteration: {iteration_count}\n"
                    "Outline:\n{outline}\n\nResearch data:\n{research_data}\n\n"
                    "Pass only if the report has enough cited evidence. If not, provide targeted follow-up search queries.",
                ),
            ]
        )
        result = self._invoke_structured(
            prompt=prompt,
            response_model=CritiqueResponse,
            payload={
                "topic": topic,
                "output_language": output_language,
                "iteration_count": iteration_count,
                "outline": "\n".join(f"- {section}" for section in outline),
                "research_data": _format_research_data_for_prompt(research_data),
            },
        )
        return result.passed, result.notes, result.follow_up_queries

    def write_report(
        self,
        topic: str,
        outline: list[str],
        research_data: list[ResearchFinding],
        critique_notes: list[str],
        language: str = "en",
    ) -> str:
        output_language = _language_name(language)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You write professional intelligence reports in Markdown. Use only the provided research data. "
                    "Write the full report in {output_language}.",
                ),
                (
                    "human",
                    "Topic: {topic}\nLanguage: {output_language}\nOutline:\n{outline}\n\n"
                    "Research data:\n{research_data}\n\nCritique notes:\n{critique_notes}\n\n"
                    "Write a polished report with headings, concise analysis, and a Sources section with URLs.",
                ),
            ]
        )
        result = self._invoke_structured(
            prompt=prompt,
            response_model=ReportResponse,
            payload={
                "topic": topic,
                "output_language": output_language,
                "outline": "\n".join(f"- {section}" for section in outline),
                "research_data": _format_research_data_for_prompt(research_data),
                "critique_notes": "\n".join(f"- {note}" for note in critique_notes),
            },
        )
        return result.markdown

    def _invoke_structured(self, prompt: ChatPromptTemplate, response_model: type[BaseModel], payload: dict) -> BaseModel:
        last_error: Exception | None = None
        for model in self.models:
            try:
                chain = prompt | model.with_structured_output(response_model)
                return chain.invoke(payload)
            except Exception as exc:
                if not _is_retryable_model_error(exc):
                    raise
                last_error = exc
        if last_error:
            raise last_error
        raise RuntimeError("No LLM models configured.")


def get_llm(settings: Settings) -> ResearchLLM:
    if settings.llm_provider == "demo":
        return DemoLLM()

    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        return LangChainResearchLLM(
            [
                ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0.2,
                )
            ]
        )

    if settings.llm_provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=gemini.")
        model_names = [settings.gemini_model] + [
            name.strip()
            for name in settings.gemini_fallback_models.split(",")
            if name.strip()
        ]
        return LangChainResearchLLM(
            [
                ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=settings.google_api_key,
                )
                for model_name in model_names
            ]
        )

    return DemoLLM()


def _format_sources_for_prompt(sources: list[ResearchSource]) -> str:
    if not sources:
        return "No sources found."
    return "\n\n".join(
        "\n".join(
            [
                f"Title: {source.get('title', 'Untitled')}",
                f"URL: {source.get('url', 'unknown')}",
                f"Snippet: {source.get('snippet', '')}",
            ]
        )
        for source in sources
    )


def _format_research_data_for_prompt(research_data: list[ResearchFinding]) -> str:
    if not research_data:
        return "No research data collected."
    return "\n\n".join(_format_finding_for_report(finding) for finding in research_data)


def _format_finding_for_report(finding: ResearchFinding) -> str:
    source_lines = [
        f"- {source.get('title', 'Untitled')}: {source.get('url', 'unknown')}"
        for source in finding.get("sources", [])
    ]
    sources = "\n".join(source_lines) or "- No sources"
    return f"Section: {finding['section']}\nSummary: {finding['summary']}\nSources:\n{sources}"


def _format_demo_finding_for_report(finding: ResearchFinding) -> str:
    return finding["summary"]


def _format_all_sources_for_report(research_data: list[ResearchFinding]) -> str:
    seen_urls: set[str] = set()
    lines: list[str] = []
    for finding in research_data:
        for source in finding.get("sources", []):
            url = source.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title = source.get("title", "Untitled")
            lines.append(f"- [{title}]({url})")
    return "\n".join(lines) or "- No sources collected."


def _language_name(language: str) -> str:
    return "Vietnamese" if language == "vi" else "English"


def _is_retryable_model_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retryable_fragments = [
        "503",
        "unavailable",
        "high demand",
        "not_found",
        "not found",
        "rate limit",
        "resource_exhausted",
        "quota",
        "retry",
        "temporarily",
    ]
    return any(fragment in message for fragment in retryable_fragments)
