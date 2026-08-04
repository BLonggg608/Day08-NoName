"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

# Dựa theo tài liệu Lab (Checkpoint 4), threshold tối ưu thường rơi vào khoảng 0.48 
# đối với model BAAI/bge-m3. Bạn có thể điều chỉnh lại sau khi test thực tế.
SCORE_THRESHOLD = 0.48  
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"  # "cross_encoder" | "mmr" | "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search → dense_results (giữ điểm cosine gốc)
          ├→ Lexical Search  → sparse_results
          │
          ├→ Merge (RRF) → merged_results
          ├→ Rerank → reranked_results
          │
          └→ If dense_results[0]["score"] < threshold:
                └→ PageIndex Vectorless → fallback_results
    """
    
    # Step 1: Song song chạy semantic + lexical
    # Lấy top_k * 2 để có pool dữ liệu đủ lớn cho quá trình reranking & fusion
    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    # Step 2: Merge bằng RRF (Reciprocal Rank Fusion)
    # Lưu ý: Hàm rerank_rrf sẽ xử lý logic gộp danh sách dict, ở đây truyền list các list
    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    
    # Gắn thẻ metadata source cho các chunks
    for item in merged:
        item["source"] = "hybrid"

    # Step 3: Rerank (Tùy chọn)
    if use_reranking and merged:
        # Giả định hàm rerank nhận method. Nếu file task7 của bạn không có param method, hãy xóa nó đi.
        try:
            final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        except TypeError:
            # Fallback nếu hàm rerank không nhận tham số method
            final_results = rerank(query, merged, top_k=top_k)
    else:
        final_results = merged[:top_k]

    # Step 4: Check threshold DÙNG ĐIỂM COSINE GỐC (dense_results), KHÔNG PHẢI RRF
    # Điều này đảm bảo Fallback được kích hoạt đúng lúc khi vector search không tự tin.
    best_score = dense_results[0]["score"] if dense_results else 0.0
    
    if best_score < score_threshold:
        print(f"  ⚠ Semantic best score ({best_score:.3f}) < threshold ({score_threshold}). Triggering Fallback...")
        fallback = pageindex_search(query, top_k=top_k)
        
        # Nếu Fallback trả về kết quả, dùng kết quả đó
        if fallback:
            for item in fallback:
                if "source" not in item:
                    item["source"] = "pageindex"
            return fallback

    # Trả về kết quả Hybrid nếu best_score >= threshold, hoặc Fallback thất bại/rỗng
    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "What is the tuition fee at RMIT Vietnam?",
        "How do I book a library study room?",
        "What scholarships are available for international students?",
        "xyzabc123nonsense",  # Query không có kết quả → test fallback
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        try:
            results = retrieve(q, top_k=3)
            if not results:
                print("  (Không tìm thấy kết quả)")
            for i, r in enumerate(results, 1):
                # Format an toàn đề phòng các key bị thiếu
                score = r.get('score', 0.0)
                source = r.get('source', 'unknown')
                content = r.get('content', '')[:80].replace('\n', ' ')
                print(f"  {i}. [{score:.3f}] [{source}] {content}...")
        except Exception as e:
            print(f"  Lỗi khi chạy query: {e}")