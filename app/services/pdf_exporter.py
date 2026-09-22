from pathlib import Path


def export_markdown_placeholder(markdown: str, output_path: Path) -> Path:
    """Phase 4 placeholder: persist Markdown until PDF rendering is wired."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path

