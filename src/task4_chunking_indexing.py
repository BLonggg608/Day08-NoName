"""
Task 4 — Chunking & Indexing vào Vector Store (ChromaDB).
"""

import shutil
from pathlib import Path

# Thư viện cần thiết
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from .embedding_provider import embed_texts, embedding_description

# Đường dẫn thư mục
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# ĐỒNG BỘ CONFIG VỚI YÊU CẦU CỦA LEADER (ROLE 1)
# =============================================================================
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = embedding_description()
COLLECTION_NAME = "university_services"


# =============================================================================
# IMPLEMENTATION (ROLE 2)
# =============================================================================

def load_documents() -> list[dict]:
    """1. Đọc toàn bộ markdown files từ data/standardized/"""
    documents = []
    
    if not STANDARDIZED_DIR.exists():
        print(f"ERROR: standardized directory not found: {STANDARDIZED_DIR}")
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Phân loại metadata theo thư mục cha (legal hay news)
        doc_type = "legal" if "legal" in md_file.parts else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """2. Dùng RecursiveCharacterTextSplitter chia nhỏ văn bản"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {**doc["metadata"], "chunk_index": i}
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """3. Embed chunks bằng SentenceTransformer BAAI/bge-m3"""
    print(f"Embedding provider: {EMBEDDING_MODEL}")
    texts = [c["content"] for c in chunks]
    
    print("Creating embeddings...")
    embeddings = embed_texts(texts)
    
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """4. Upsert chunks + embeddings vào ChromaDB persistent"""
    # ⚡ Lưu ý của Leader: Xoá thư mục chroma_db cũ trước khi tạo mới
    if CHROMA_DIR.exists():
        print("Removing existing ChromaDB...")
        shutil.rmtree(CHROMA_DIR)
        
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Khởi tạo Chroma Client Persistent
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Tạo collection, ép buộc dùng không gian Cosine Distance
    # Ở bước Retrieval, ta sẽ tính Score = 1.0 - Distance
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Tạo ID duy nhất cho mỗi chunk
    ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
    
    print("Writing vectors to ChromaDB...")
    collection.upsert(
        ids=ids,
        documents=[c["content"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def run_pipeline():
    """Chạy toàn bộ pipeline Task 4."""
    print("=" * 50)
    print("Task 4: Chunking and Indexing")
    print(f"Config: chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    print(f"Embedding: {EMBEDDING_MODEL}")
    print(f"Collection: {COLLECTION_NAME}")
    print("=" * 50)

    docs = load_documents()
    if not docs:
        print("ERROR: no input documents. Run Task 3 first.")
        return
    print(f"Loaded {len(docs)} Markdown files.")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    chunks = embed_chunks(chunks)
    print(f"Created {len(chunks)} embeddings.")

    index_to_vectorstore(chunks)
    print(f"Done. ChromaDB saved at: {CHROMA_DIR.absolute()}")


if __name__ == "__main__":
    run_pipeline()
