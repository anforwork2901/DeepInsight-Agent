from app.graph import build_graph, build_research_graph


def test_graph_generates_report():
    graph = build_graph()
    result = graph.invoke({"topic": "AI in supply chain", "depth": "quick"})

    assert result["final_report"].startswith("# AI in supply chain")
    assert result["iteration_count"] >= 1


def test_research_graph_resumes_after_planning():
    graph = build_research_graph()
    result = graph.invoke(
        {
            "topic": "AI in supply chain",
            "depth": "quick",
            "outline": ["Market context", "Risks"],
            "iteration_count": 0,
        }
    )

    assert result["final_report"].startswith("# AI in supply chain")
    assert result["outline"] == ["Market context", "Risks"]


def test_graph_generates_vietnamese_report():
    graph = build_graph()
    result = graph.invoke(
        {
            "topic": "Rào cản ứng dụng AI trong doanh nghiệp SME Việt Nam",
            "depth": "quick",
            "report_language": "vi",
        }
    )

    assert "## Nguồn tham khảo" in result["final_report"]
    assert "Tóm tắt điều hành" in result["final_report"]
