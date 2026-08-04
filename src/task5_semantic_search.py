"""Task 5 — Semantic Search và HyDE trên ChromaDB."""

import os

import chromadb
from dotenv import load_dotenv
from .embedding_provider import embed_texts

from .task4_chunking_indexing import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)

load_dotenv()

HYDE_MODEL = os.getenv("HYDE_MODEL", "openai/gpt-4o-mini")
HYDE_SYSTEM_PROMPT = """Bạn là trợ lý viết tài liệu phục vụ tìm kiếm ngữ nghĩa.
Hãy viết một đoạn văn ngắn có khả năng xuất hiện trong tài liệu và trả lời trực tiếp
câu hỏi của người dùng. Không thêm lời dẫn, không nêu rằng đây là câu trả lời giả định."""


def _get_collection():
    """Mở collection đã được Task 4 tạo; trả None nếu chưa index dữ liệu."""
    if not CHROMA_DIR.exists():
        return None

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception as exc:
        # ChromaDB thay đổi kiểu exception giữa các phiên bản.
        if "does not exist" in str(exc).lower() or "not found" in str(exc).lower():
            return None
        raise


def _generate_hypothetical_doc(query: str) -> str:
    """Sinh hypothetical document bằng OpenRouter; lỗi thì dùng lại query gốc."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "sk-or-v1-...":
        return query

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            model=HYDE_MODEL,
            messages=[
                {"role": "system", "content": HYDE_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            max_tokens=250,
        )
        hypothetical_doc = response.choices[0].message.content
        return hypothetical_doc.strip() if hypothetical_doc else query
    except Exception as exc:
        print(f"WARNING: HyDE unavailable; using original query: {exc}")
        return query


def _search_text(search_text: str, top_k: int) -> list[dict]:
    """Embed văn bản và tìm các chunk gần nhất trong ChromaDB."""
    collection = _get_collection()
    if collection is None:
        return []

    collection_size = collection.count()
    if collection_size == 0:
        return []

    query_vector = embed_texts([search_text])[0]
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection_size),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    output = []
    for document, metadata, distance in zip(
        documents[0], metadatas[0], distances[0]
    ):
        # Chroma cosine distance = 1 - cosine similarity.
        score = max(0.0, 1.0 - float(distance))
        output.append(
            {
                "content": document,
                "score": round(score, 4),
                "metadata": metadata or {},
            }
        )

    output.sort(key=lambda item: item["score"], reverse=True)
    return output[:top_k]


def semantic_search(
    query: str,
    top_k: int = 10,
    use_hyde: bool = False,
) -> list[dict]:
    """Tìm kiếm dense bằng cosine similarity, có thể mở rộng query bằng HyDE."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []

    query = query.strip()
    search_text = _generate_hypothetical_doc(query) if use_hyde else query
    return _search_text(search_text, top_k)


def hyde_search(query: str, top_k: int = 10) -> list[dict]:
    """Shortcut cho semantic search có bật Hypothetical Document Embeddings."""
    return semantic_search(query, top_k=top_k, use_hyde=True)


if __name__ == "__main__":
    results = semantic_search("what is the tuition fee", top_k=5)
    for result in results:
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
