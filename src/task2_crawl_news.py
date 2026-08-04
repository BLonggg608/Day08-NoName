"""
Task 2 — Crawl bài viết/thông báo về dịch vụ đại học.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết từ trang công khai của một trường đại học.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
    playwright install chromium   # bắt buộc — pip install crawl4ai KHÔNG tự tải browser binary,
                                   # thiếu bước này sẽ báo lỗi
                                   # "BrowserType.launch: Executable doesn't exist"

Gợi ý chủ đề: thông báo tuyển sinh, sự kiện, dịch vụ thư viện, hỗ trợ sinh viên, học bổng.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


ARTICLE_URLS = [
    "https://www.rmit.edu.vn/vi/tin-tuc/tat-ca-tin-tuc/2026/may/sinh-vien-rmit-duoc-trao-hoc-bong-voices-of-the-future-fellow-dau-tien",
    "https://www.rmit.edu.vn/vi/tin-tuc/tat-ca-tin-tuc/2026/jan/dai-hoc-rmit-viet-nam-cong-bo-chuong-trinh-hoc-bong-ky-luc-tri-gia-hon-200-ti-dong",
    "https://www.rmit.edu.vn/vi/tin-tuc/tat-ca-tin-tuc/2026/mar/dai-hoc-rmit-dau-tu-manh-vao-nghien-cuu-voi-65-hoc-bong-tien-si",
    "https://www.rmit.edu.vn/vi/tin-tuc/tat-ca-tin-tuc/2025/oct/rmit-viet-nam-trao-hoc-bong-tri-gia-47-5-ti-dong-nam-2025",
    "https://www.rmit.edu.vn/vi/tin-tuc/tat-ca-tin-tuc/2020/thang-1/binh-dang-giao-duc-cho-moi-sinh-vien",
    "https://www.rmit.edu.vn/vi/tin-tuc/tat-ca-tin-tuc/2022/nov/sinh-vien-hoc-bong-tim-thay-suc-manh-tu-y-tuong-duoc-lan-toa",
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    if not result.success:
        error = getattr(result, "error_message", "Unknown crawl error")
        raise RuntimeError(f"Không thể crawl {url}: {error}")

    # Crawl4AI mới trả về MarkdownGenerationResult, phiên bản cũ trả về str.
    markdown_result = result.markdown
    content = getattr(markdown_result, "fit_markdown", None)
    if not content:
        content = getattr(markdown_result, "raw_markdown", None)
    if not content:
        content = str(markdown_result or "")

    content = content.strip()
    if not content:
        raise RuntimeError(f"Trang {url} không có nội dung Markdown")

    metadata = result.metadata or {}
    return {
        "url": result.url or url,
        "title": metadata.get("title") or "Unknown",
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": content,
    }


async def crawl_all():
    """Crawl toàn bộ bài viết trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2))
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm trang thông báo/sự kiện trên trang chính thức của trường đại học")
    else:
        asyncio.run(crawl_all())
