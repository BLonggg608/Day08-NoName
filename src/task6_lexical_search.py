"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from pathlib import Path
import re

import numpy as np
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}
BM25_INDEX = None


class SimpleBM25Okapi:
    """Fallback BM25 khi môi trường chưa cài rank-bm25."""

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_len = np.array([len(doc) for doc in tokenized_corpus], dtype=float)
        self.avgdl = float(np.mean(self.doc_len)) if len(self.doc_len) else 0.0
        self.doc_freqs = []
        document_frequency = {}

        for doc in tokenized_corpus:
            frequencies = {}
            for token in doc:
                frequencies[token] = frequencies.get(token, 0) + 1
            self.doc_freqs.append(frequencies)
            for token in frequencies:
                document_frequency[token] = document_frequency.get(token, 0) + 1

        doc_count = len(tokenized_corpus)
        self.idf = {
            token: np.log(1 + (doc_count - freq + 0.5) / (freq + 0.5))
            for token, freq in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> np.ndarray:
        scores = np.zeros(len(self.corpus), dtype=float)
        if not self.corpus or self.avgdl == 0:
            return scores

        for token in query_tokens:
            idf = self.idf.get(token, 0.0)
            if idf == 0.0:
                continue
            for idx, frequencies in enumerate(self.doc_freqs):
                term_frequency = frequencies.get(token, 0)
                if term_frequency == 0:
                    continue
                denominator = term_frequency + self.k1 * (
                    1 - self.b + self.b * self.doc_len[idx] / self.avgdl
                )
                scores[idx] += idf * (term_frequency * (self.k1 + 1)) / denominator
        return scores


def _tokenize(text: str) -> list[str]:
    """Tokenize đơn giản cho lexical search tiếng Việt/tiếng Anh."""
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _load_corpus() -> list[dict]:
    """Load corpus từ markdown đã chuẩn hoá và chia thành chunks."""
    corpus = []
    if not STANDARDIZED_DIR.exists():
        return corpus

    step = CHUNK_SIZE - CHUNK_OVERLAP
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in md_file.parts else "news"
        for chunk_index, start in enumerate(range(0, len(content), step)):
            chunk = content[start:start + CHUNK_SIZE].strip()
            if not chunk:
                continue
            corpus.append({
                "content": chunk,
                "metadata": {
                    "source": md_file.name,
                    "type": doc_type,
                    "chunk_index": chunk_index,
                },
            })
    return corpus


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    bm25_cls = BM25Okapi or SimpleBM25Okapi
    return bm25_cls(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    global CORPUS, BM25_INDEX

    if not query.strip() or top_k <= 0:
        return []

    if not CORPUS:
        CORPUS = _load_corpus()
    if not CORPUS:
        return []

    if BM25_INDEX is None:
        BM25_INDEX = build_bm25_index(CORPUS)

    scores = BM25_INDEX.get_scores(_tokenize(query))
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        results.append({
            "content": CORPUS[idx]["content"],
            "score": score,
            "metadata": CORPUS[idx].get("metadata", {}),
        })

    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("tuition fee payment methods", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
