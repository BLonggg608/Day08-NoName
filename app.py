"""
RAG Chatbot — University Services (Starter Template)
Streamlit app kết nối RAG Retrieval (Task 9) và Generation (Task 10).

Chạy:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Initialize session state before rendering sidebar widgets.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Thêm project root vào sys.path để import các task từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="University Services RAG Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# COMIC BOOK / GAME STYLE THEME
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@400;700&display=swap');

    :root {
        --cx-yellow: #F4E7B8;
        --cx-red: #C62828;
        --cx-blue: #185ADB;
        --cx-black: #17202A;
        --cx-white: #FFFFFF;
        --cx-panel: #FFFDF5;
    }

    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stBottomBlockContainer"] {
        background-color: var(--cx-yellow) !important;
        background-image: radial-gradient(circle, rgba(23,32,42,0.08) 1.2px, transparent 1.2px) !important;
        background-size: 18px 18px !important;
    }

    [data-testid="stHeader"] { box-shadow: none; }
    [data-testid="stDecoration"] { background-image: none !important; }

    html, body, [class*="css"] {
        font-family: "Comic Neue", "Comic Sans MS", cursive, sans-serif;
        color: var(--cx-black);
    }

    p, span, div, label {
        color: var(--cx-black);
        font-weight: 700;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #333 !important;
    }

    /* Comic-style headers */
    h1, h2, h3 {
        font-family: "Bangers", "Comic Neue", cursive !important;
        letter-spacing: 0.03em;
        color: var(--cx-red) !important;
        -webkit-text-stroke: 1.5px var(--cx-black);
        text-shadow: 3px 3px 0 var(--cx-black);
    }

    /* Main page title — comic caption box, optimized for readability */
    .main-title-box {
        display: inline-block;
        background-color: var(--cx-white);
        border: 4px solid var(--cx-black);
        border-radius: 12px;
        padding: 10px 24px;
        margin-bottom: 6px;
        box-shadow: 6px 6px 0 var(--cx-black);
    }
    .main-title-box h1 {
        font-family: "Bangers", "Comic Neue", cursive !important;
        font-size: 2.4rem;
        letter-spacing: 0.04em;
        color: var(--cx-black) !important;
        -webkit-text-stroke: 0;
        text-shadow: none;
        margin: 0;
        line-height: 1.2;
    }

    /* Sidebar as a comic panel with thick border */
    section[data-testid="stSidebar"] {
        background-color: var(--cx-panel);
        border-right: 3px solid var(--cx-black);
    }
    section[data-testid="stSidebar"] h3 {
        color: var(--cx-blue) !important;
        -webkit-text-stroke: 1px var(--cx-black);
    }

    /* Sidebar suggestion buttons -> comic action buttons, tilted for comic effect */
    section[data-testid="stSidebar"] .stButton {
        margin-bottom: 14px;
        transition: transform 0.12s ease-in-out;
    }
    section[data-testid="stSidebar"] .stButton:nth-of-type(5n+1) { transform: rotate(-3deg); }
    section[data-testid="stSidebar"] .stButton:nth-of-type(5n+2) { transform: rotate(2.5deg); }
    section[data-testid="stSidebar"] .stButton:nth-of-type(5n+3) { transform: rotate(-2deg); }
    section[data-testid="stSidebar"] .stButton:nth-of-type(5n+4) { transform: rotate(3deg); }
    section[data-testid="stSidebar"] .stButton:nth-of-type(5n+5) { transform: rotate(-1.5deg); }
    section[data-testid="stSidebar"] .stButton:hover {
        transform: rotate(0deg) scale(1.04);
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: var(--cx-blue);
        border: 3px solid var(--cx-black);
        border-radius: 10px;
        text-align: left;
        font-weight: 800;
        font-family: "Comic Neue", cursive;
        padding: 8px 14px;
        box-shadow: 4px 4px 0 var(--cx-black);
        transition: all 0.08s ease-in-out;
    }
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stButton > button p,
    section[data-testid="stSidebar"] .stButton > button span,
    section[data-testid="stSidebar"] .stButton > button div {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: var(--cx-red);
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 0 var(--cx-black);
    }
    section[data-testid="stSidebar"] .stButton > button:active {
        transform: translate(4px, 4px);
        box-shadow: 0px 0px 0 var(--cx-black);
    }

    /* Slider accent */
    .stSlider [data-baseweb="slider"] > div > div {
        background: var(--cx-red) !important;
    }

    /* Retrieval mode selector: outlined when idle, accent-filled when selected. */
    [data-testid="stRadio"] [role="radiogroup"] {
        gap: 8px;
    }
    [data-testid="stRadio"] [role="radiogroup"] > label {
        border: 2px solid var(--cx-black);
        border-radius: 8px;
        padding: 8px 10px;
        background: transparent;
        color: var(--cx-black) !important;
        transition: background-color 0.12s ease-in-out, color 0.12s ease-in-out;
    }
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
        background: var(--cx-red);
        color: var(--cx-white) !important;
    }
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) span,
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) div {
        color: var(--cx-white) !important;
    }

    /* Chat input styled like a comic caption box */
    [data-testid="stChatInput"] {
        border: 3px solid var(--cx-black) !important;
        border-radius: 14px !important;
        box-shadow: 4px 4px 0 var(--cx-black);
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: none !important;
        background-color: var(--cx-white) !important;
        color: var(--cx-black) !important;
        font-family: "Comic Neue", cursive !important;
        font-weight: 700;
    }

    /* Chat bubbles — comic speech bubbles with a tail */
    [data-testid="stChatMessage"] {
        position: relative;
        border-radius: 20px;
        border: 3px solid var(--cx-black);
        padding: 8px 16px;
        margin-bottom: 22px;
        box-shadow: 5px 5px 0 var(--cx-black);
    }
    [data-testid="stChatMessage"]:nth-of-type(odd) {
        background-color: var(--cx-blue);
        color: white;
        margin-left: 40px;
    }
    [data-testid="stChatMessage"]:nth-of-type(odd) p,
    [data-testid="stChatMessage"]:nth-of-type(odd) span,
    [data-testid="stChatMessage"]:nth-of-type(odd) div {
        color: white;
    }
    [data-testid="stChatMessage"]:nth-of-type(odd)::after {
        content: "";
        position: absolute;
        left: -16px;
        bottom: 10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-right-color: var(--cx-black);
        border-left: 0;
    }
    [data-testid="stChatMessage"]:nth-of-type(odd)::before {
        content: "";
        position: absolute;
        left: -12px;
        bottom: 12px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-right-color: var(--cx-blue);
        border-left: 0;
        z-index: 1;
    }
    [data-testid="stChatMessage"]:nth-of-type(even) {
        background-color: var(--cx-white);
        color: var(--cx-black);
        margin-right: 40px;
    }
    [data-testid="stChatMessage"]:nth-of-type(even)::after {
        content: "";
        position: absolute;
        right: -16px;
        bottom: 10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-left-color: var(--cx-black);
        border-right: 0;
    }
    [data-testid="stChatMessage"]:nth-of-type(even)::before {
        content: "";
        position: absolute;
        right: -12px;
        bottom: 12px;
        width: 0;
        height: 0;
        border: 8px solid transparent;
        border-left-color: var(--cx-white);
        border-right: 0;
        z-index: 1;
    }

    /* Dividers as bold comic rules */
    hr {
        border: none;
        border-top: 3px solid var(--cx-black);
    }

    /* Expander (sources) as a comic caption box */
    [data-testid="stExpander"] {
        background-color: var(--cx-panel);
        border: 3px solid var(--cx-black);
        border-radius: 10px;
        box-shadow: 4px 4px 0 var(--cx-black);
    }

    /* Keep source text readable on the cream expander background. */
    [data-testid="stExpander"],
    [data-testid="stExpander"] p,
    [data-testid="stExpander"] span,
    [data-testid="stExpander"] div {
        color: var(--cx-black) !important;
    }
    [data-testid="stExpander"] code {
        color: #333333 !important;
        background-color: #F1E8C8 !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR — INFO & SETTINGS
# =============================================================================

with st.sidebar:
    st.title("🎓 University Services RAG")
    st.caption("Trợ lý hỏi đáp về dịch vụ và chính sách đại học")

    st.divider()

    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Student Fees & Charges Guide được cập nhật lần cuối vào ngày nào?",
        "Ai ban hành Student Fees & Charges Guide?",
        "Student Fees & Charges Guide có mục Tuition Fees không?",
        "Brochure dành cho nhóm sinh viên nào?",
        "Chương trình Voices of the Future Fellow kéo dài bao lâu?",
    ]
    for index, s in enumerate(suggestions):
        if st.button(
            s,
            use_container_width=True,
            key=f"suggestion_{index}",
            disabled=st.session_state.is_processing,
        ):
            st.session_state["pending_query"] = s
            st.session_state.is_processing = True
            st.rerun()

    st.divider()
    # st.subheader("⚙️ Thiết lập")  
    top_k = st.slider("Số chunks retrieval (top_k)", 3, 10, 5)
    retrieval_mode = st.radio(
        "Chế độ retrieval",
        options=["Hybrid + Rerank", "Hybrid không Rerank"],
        index=0,
        disabled=st.session_state.is_processing,
    )
    use_reranking = retrieval_mode == "Hybrid + Rerank"

    st.divider()
    # st.caption("**Kiến trúc hệ thống:**")
    # st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")

# =============================================================================
# SESSION STATE
# =============================================================================

# =============================================================================
# MAIN CHAT AREA
# =============================================================================

st.markdown(
    '<div class="main-title-box"><h1>🎓 University Services RAG Chatbot</h1></div>',
    unsafe_allow_html=True,
)
st.caption("Hệ thống hỏi đáp thông tin dịch vụ đại học")

AVATARS = {
    "user": str(PROJECT_ROOT / "spidey.png"),
    "assistant": str(PROJECT_ROOT / "iron-man.png"),
}

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATARS.get(msg["role"])):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Unknown")
                    doc_type = meta.get("type", "unknown")
                    score = src.get("score", 0)
                    st.markdown(f"**[{i}] {source_name}** `{doc_type}` | score: `{score:.4f}`")
                    st.text(src.get("content", "")[:300] + "...")
                    st.divider()

# =============================================================================
# QUERY HANDLING
# =============================================================================

# Xử lý khi bấm nút gợi ý hoặc nhập câu hỏi mới
user_input = st.chat_input(
    "Đang xử lý câu hỏi..." if st.session_state.is_processing
    else "Nhập câu hỏi của bạn về chính sách/dịch vụ đại học...",
    disabled=st.session_state.is_processing,
)

# Move a newly submitted chat query to a second run so the input and
# suggestion buttons are visibly disabled before the model call starts.
if user_input and not st.session_state.is_processing:
    st.session_state.pending_query = user_input
    st.session_state.is_processing = True
    st.rerun()

query = st.session_state.pending_query if st.session_state.is_processing else None

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                from src.task10_generation import generate_with_citation
                response = generate_with_citation(
                    query,
                    top_k=top_k,
                    use_reranking=use_reranking,
                    conversation_history=st.session_state.messages[:-1],
                )
                answer = response.get("answer", "Chưa thể trả lời.")
                sources = response.get("sources", [])

            except NotImplementedError:
                answer = "⚠️ **Task 10 chưa được implement.** Hãy hoàn thành `src/task10_generation.py` để kết nối pipeline vào UI!"
                sources = []
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        st.markdown(f"**[{i}] {source_name}** `{doc_type}` | score: `{score:.4f}`")
                        st.text(src.get("content", "")[:300] + "...")
                        st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
    st.session_state.is_processing = False
    # Re-render widgets so chat input and suggestions become enabled again.
    st.rerun()
