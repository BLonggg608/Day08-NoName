"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import os
import json
import re
import time
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_PATH = Path(__file__).parent.parent / "pageindex_doc_ids.json"
TMP_UPLOAD_DIR = Path(__file__).parent.parent / "tmp" / "pageindex_uploads"
POLL_INTERVAL_SECONDS = 2
POLL_TIMEOUT_SECONDS = 60


def _load_doc_id_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_doc_id_cache(cache: dict) -> None:
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _get_pageindex_client():
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Missing PAGEINDEX_API_KEY")
    try:
        from pageindex.client import PageIndexClient
    except ImportError as exc:
        raise RuntimeError("Missing pageindex SDK. Install with: pip install pageindex") from exc
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def _safe_pdf_text(text: str) -> str:
    """fpdf core fonts only support latin-1, so strip unsupported chars."""
    return text.encode("latin-1", errors="ignore").decode("latin-1")


def _markdown_to_pdf(md_file: Path) -> Path:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError("Missing fpdf2. Install with: pip install fpdf2") from exc

    TMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = TMP_UPLOAD_DIR / f"{md_file.stem}.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for line in md_file.read_text(encoding="utf-8").splitlines():
        line = _safe_pdf_text(line).strip()
        if not line:
            pdf.ln(4)
            continue
        pdf.multi_cell(0, 6, line)

    pdf.output(str(pdf_path))
    return pdf_path


def _extract_doc_id(response) -> str | None:
    if not isinstance(response, dict):
        return None
    return (
        response.get("doc_id")
        or response.get("document_id")
        or response.get("id")
        or response.get("data", {}).get("doc_id")
        or response.get("data", {}).get("id")
    )


def _submit_document(client, file_path: Path) -> dict:
    for method_name in ("submit_document", "upload_document", "upload"):
        method = getattr(client, method_name, None)
        if method:
            return method(str(file_path))
    raise RuntimeError("PageIndex client has no supported document upload method")


def _submit_query(client, doc_id: str, query: str) -> dict:
    for method_name in ("submit_query", "query", "create_retrieval"):
        method = getattr(client, method_name, None)
        if method:
            return method(doc_id=doc_id, query=query)
    raise RuntimeError("PageIndex client has no supported query method")


def _get_retrieval(client, retrieval_id: str) -> dict:
    for method_name in ("get_retrieval", "get_query", "retrieve"):
        method = getattr(client, method_name, None)
        if method:
            return method(retrieval_id)
    raise RuntimeError("PageIndex client has no supported retrieval polling method")


def _extract_retrieval_id(response: dict) -> str | None:
    return (
        response.get("retrieval_id")
        or response.get("query_id")
        or response.get("id")
        or response.get("data", {}).get("retrieval_id")
        or response.get("data", {}).get("id")
    )


def _poll_retrieval(client, retrieval_id: str) -> dict:
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    last_response = {}

    while time.time() < deadline:
        last_response = _get_retrieval(client, retrieval_id)
        status = str(last_response.get("status", "")).lower()
        if status in {"completed", "complete", "succeeded", "success"}:
            return last_response
        if status in {"failed", "error", "cancelled"}:
            raise RuntimeError(f"PageIndex retrieval failed: {last_response}")
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"PageIndex retrieval timed out: {last_response}")


def _parse_pageindex_response(retrieval: dict, top_k: int) -> list[dict]:
    results = []
    nodes = retrieval.get("retrieved_nodes") or retrieval.get("nodes") or []

    for node_rank, node in enumerate(nodes, start=1):
        relevant_contents = node.get("relevant_contents") or []
        for group in relevant_contents:
            items = group if isinstance(group, list) else [group]
            for item in items:
                if not isinstance(item, dict):
                    continue
                content = item.get("relevant_content") or item.get("content") or ""
                if not content.strip():
                    continue
                results.append({
                    "content": content,
                    "score": 1.0 / node_rank,
                    "metadata": {
                        "section": item.get("section_title"),
                        "doc_id": node.get("doc_id") or node.get("document_id"),
                    },
                    "source": "pageindex",
                })
                if len(results) >= top_k:
                    return results

    return results[:top_k]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower(), flags=re.UNICODE))


def _local_vectorless_search(query: str, top_k: int) -> list[dict]:
    """Local fallback mô phỏng retrieval theo section khi chưa cấu hình PageIndex."""
    query_terms = _tokenize(query)
    if not query_terms or not STANDARDIZED_DIR.exists():
        return []

    candidates = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        current_title = md_file.stem
        buffer = []

        def flush_section():
            if not buffer:
                return
            content = "\n".join(buffer).strip()
            overlap = len(query_terms & _tokenize(content))
            if overlap > 0:
                candidates.append({
                    "content": content[:1200],
                    "score": overlap / max(len(query_terms), 1),
                    "metadata": {
                        "section": current_title,
                        "source": md_file.name,
                        "fallback": "local_section_search",
                    },
                    "source": "pageindex",
                })

        for line in md_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                flush_section()
                current_title = line.lstrip("#").strip() or md_file.stem
                buffer = [line]
            else:
                buffer.append(line)
        flush_section()

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:top_k]


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    client = _get_pageindex_client()
    cache = _load_doc_id_cache()

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        cache_key = str(md_file.relative_to(STANDARDIZED_DIR))
        if cache_key in cache:
            print(f"  ✓ Cached: {cache_key} -> {cache[cache_key]}")
            continue

        pdf_path = _markdown_to_pdf(md_file)
        response = _submit_document(client, pdf_path)
        doc_id = _extract_doc_id(response)
        if not doc_id:
            raise RuntimeError(f"Cannot find doc_id in PageIndex response: {response}")

        cache[cache_key] = doc_id
        _save_doc_id_cache(cache)
        print(f"  ✓ Uploaded: {cache_key} -> {doc_id}")

    return cache


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not query.strip() or top_k <= 0:
        return []

    try:
        client = _get_pageindex_client()
        doc_ids = list(_load_doc_id_cache().values())
        if not doc_ids:
            doc_ids = list(upload_documents().values())

        results = []
        for doc_id in doc_ids:
            query_response = _submit_query(client, doc_id, query)
            retrieval_id = _extract_retrieval_id(query_response)
            retrieval = (
                _poll_retrieval(client, retrieval_id)
                if retrieval_id
                else query_response
            )
            results.extend(_parse_pageindex_response(retrieval, top_k - len(results)))
            if len(results) >= top_k:
                break
        return results[:top_k]
    except Exception as exc:
        print(f"  ⚠ PageIndex unavailable, using local fallback: {exc}")
        return _local_vectorless_search(query, top_k)


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("tuition fee payment methods", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
