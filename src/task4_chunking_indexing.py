"""
Task 4 — Chunking & Indexing vào Vector Store (ChromaDB).
"""

import shutil
from pathlib import Path

# Thư viện cần thiết
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

# Đường dẫn thư mục
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# ĐỒNG BỘ CONFIG VỚI YÊU CẦU CỦA LEADER (ROLE 1)
# =============================================================================
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "BAAI/bge-m3" 
COLLECTION_NAME = "university_services"


# =============================================================================
# IMPLEMENTATION (ROLE 2)
# =============================================================================

def load_documents() -> list[dict]:
    """1. Đọc toàn bộ markdown files từ data/standardized/"""
    documents = []
    
    if not STANDARDIZED_DIR.exists():
        print(f"❌ Thư mục không tồn tại: {STANDARDIZED_DIR}")
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
    print(f"⏳ Đang tải mô hình '{EMBEDDING_MODEL}'...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [c["content"] for c in chunks]
    
    print("⏳ Đang mã hóa vector (Embedding)...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """4. Upsert chunks + embeddings vào ChromaDB persistent"""
    # ⚡ Lưu ý của Leader: Xoá thư mục chroma_db cũ trước khi tạo mới
    if CHROMA_DIR.exists():
        print("🧹 Đang xóa ChromaDB cũ để tránh rác (theo yêu cầu Leader)...")
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
    
    print("⏳ Đang Upsert dữ liệu vào ChromaDB...")
    collection.upsert(
        ids=ids,
        documents=[c["content"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def run_pipeline():
    """Chạy toàn bộ pipeline Task 4."""
    print("=" * 50)
    print("🚀 Bắt đầu Task 4: Chunking & Indexing")
    print(f"⚙️ Config: {CHUNK_SIZE} size, {CHUNK_OVERLAP} overlap")
    print(f"🧠 Model: {EMBEDDING_MODEL}")
    print(f"🗄️ Collection: {COLLECTION_NAME}")
    print("=" * 50)

    docs = load_documents()
    if not docs:
        print("❌ Lỗi: Không có dữ liệu đầu vào. Hãy chắc chắn Task 3 đã chạy thành công!")
        return
    print(f"✓ Đã đọc {len(docs)} files markdown.")

    chunks = chunk_documents(docs)
    print(f"✓ Đã chia thành {len(chunks)} chunks.")

    chunks = embed_chunks(chunks)
    print(f"✓ Đã nhúng (embed) thành công {len(chunks)} vectors.")

    index_to_vectorstore(chunks)
    print(f"🎉 HOÀN THÀNH! Dữ liệu đã được lưu an toàn tại: {CHROMA_DIR.absolute()}")


if __name__ == "__main__":
    run_pipeline()
