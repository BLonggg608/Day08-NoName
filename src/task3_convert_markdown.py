"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install "markitdown[pdf]"
    # Lưu ý: cần extra [pdf] để convert được file PDF. Chỉ "pip install markitdown"
    # (không có extra) sẽ báo MissingDependencyException khi convert PDF, dù JSON/DOCX
    # vẫn convert bình thường.

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
import re
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None
from pypdf import PdfReader

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def clean_extracted_text(text: str) -> str:
    """Make PDF text readable without changing its factual content."""
    text = text.replace("\x0c", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown() if MarkItDown else None

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            if md is not None:
                result = md.convert(str(filepath))
                extracted = result.text_content
            else:
                reader = PdfReader(str(filepath))
                pages = []
                for page_no, page in enumerate(reader.pages, 1):
                    try:
                        raw_text = page.extract_text(extraction_mode="layout") or ""
                    except TypeError:
                        raw_text = page.extract_text() or ""
                    text = clean_extracted_text(raw_text)
                    if text:
                        pages.append(f"## Page {page_no}\n\n{text}")
                extracted = "\n\n".join(pages)
            output_path = output_dir / f"{filepath.stem}.md"
            header = f"# {filepath.stem}\n\n**Source file:** `{filepath.name}`\n\n---\n\n"
            output_path.write_text(header + clean_extracted_text(extracted) + "\n", encoding="utf-8")
            print(f"  Saved: {output_path}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            title = data.get("title") or filepath.stem
            source = data.get("url") or data.get("source_url") or "N/A"
            crawled = data.get("date_crawled") or data.get("crawled_at") or "N/A"
            content = data.get("content_markdown") or data.get("content") or data.get("text") or ""
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False, indent=2)
            header = f"# {title}\n\n**Source:** {source}\n**Crawled:** {crawled}\n\n---\n\n"
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(header + str(content).strip() + "\n", encoding="utf-8")
            print(f"  Saved: {output_path}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\nDone! Output tai:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
