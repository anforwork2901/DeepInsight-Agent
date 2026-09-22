# DeepInsight Agent

Autonomous Deep Research & Intelligence Agent built with LangGraph.

The project will evolve in six phases:

1. Project foundation, configuration, and state schema.
2. Core multi-node LangGraph workflow.
3. Human-in-the-loop review with SQLite checkpointing.
4. LangSmith tracing and PDF export.
5. Streamlit interface.
6. Docker packaging and portfolio-ready documentation.

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main "AI adoption trends in Vietnamese SMEs"
```

The initial version can run with deterministic demo services before API keys are configured.

## Low-Quota Mode

When LLM credits or free-tier quotas are limited, use Tavily for real web search while keeping the LLM deterministic:

```bash
LLM_PROVIDER=demo
TAVILY_API_KEY=your_tavily_key
```

This mode still exercises the LangGraph workflow and real retrieval layer, but avoids paid LLM calls.

## MySQL Persistence

Create the local database in MySQL Workbench by running:

```sql
source db/schema.sql;
```

Then enable persistence in `.env`:

```bash
MYSQL_ENABLED=true
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=deepinsight_agent
```

When enabled, each CLI run is saved to MySQL with its topic, outline, research sources, critique notes, final report, and output path.

## Human-In-The-Loop CLI

Run the workflow with outline approval before web research:

```bash
python -m app.hitl_cli "AI adoption trends in Vietnamese SMEs" --depth quick
```

The CLI stores the planned outline as `awaiting_human`, waits for approval or feedback, then resumes from the research step and updates the same MySQL run to `completed`.

Generate Vietnamese output:

```bash
python -m app.hitl_cli "Rào cản ứng dụng AI trong doanh nghiệp SME Việt Nam" --depth quick --language vi
```

## Streamlit UI

Run the interactive HITL dashboard:

```bash
streamlit run ui/streamlit_app.py
```

The UI supports outline generation, feedback, approval, research execution, Markdown download, and recent MySQL run history.

## Phase 2: Real LLM and Search

The graph now uses service adapters:

- `app/services/llm.py`: wraps OpenAI or Gemini through LangChain chat models.
- `app/services/search.py`: wraps Tavily Search behind a simple `search(query)` interface.
- `app/nodes/researcher.py`: searches sources and asks the LLM to summarize evidence.
- `app/nodes/critic.py`: asks the LLM to decide whether more research is needed.
- `app/nodes/writer.py`: asks the LLM to produce a Markdown report grounded in collected sources.

To enable real APIs, edit `.env`:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4.1-mini
TAVILY_API_KEY=your_tavily_key
```

Or use Gemini:

```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_key
GEMINI_MODEL=gemini-3.6-flash
GEMINI_FALLBACK_MODELS=
TAVILY_API_KEY=your_tavily_key
```

Then run:

```bash
python -m app.main "AI adoption trends in Vietnamese SMEs" --depth deep
```
