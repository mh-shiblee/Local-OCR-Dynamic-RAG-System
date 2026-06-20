import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Local OCR & RAG System",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Local OCR & RAG System")
st.caption("Multilingual document search — Bangla & English, fully local.")

# ─── Sidebar: Upload ────────────────────────────────────────────────────────

with st.sidebar:
    st.header("📄 Upload Document")

    uploaded_file = st.file_uploader(
        "Choose a PDF or image",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    doc_type = st.selectbox(
        "Document Type",
        ["general", "letter", "cv", "report", "invoice", "form", "other"]
    )

    doc_date = st.date_input("Document Date")

    upload_btn = st.button("Upload & Process", use_container_width=True)

    if upload_btn and uploaded_file:
        with st.spinner("Running OCR and processing..."):
            response = requests.post(
                f"{API_URL}/upload",
                files={"file": (uploaded_file.name,
                                uploaded_file.getvalue(), uploaded_file.type)},
                data={
                    "doc_type": doc_type,
                    "doc_date": str(doc_date)
                }
            )
            result = response.json()

        if "error" in result:
            st.error(result["error"])
        else:
            st.success("Document processed!")
            st.json(result)

    elif upload_btn and not uploaded_file:
        st.warning("Please select a file first.")

    st.divider()

    # ─── Uploaded Documents List ────────────────────────────────────────────
    st.header("🗂️ Uploaded Documents")
    if st.button("Refresh List", use_container_width=True):
        docs = requests.get(f"{API_URL}/documents").json()
        if docs["documents"]:
            for doc in docs["documents"]:
                st.markdown(f"""
                **{doc['filename']}**
                - 🌐 Language: `{doc['language']}`
                - 📁 Type: `{doc['doc_type']}`
                - 📅 Date: `{doc['doc_date']}`
                """)
        else:
            st.info("No documents uploaded yet.")


# ─── Main Area: Query ───────────────────────────────────────────────────────

st.header("💬 Ask a Question")

query = st.text_area(
    "Enter your question",
    placeholder="e.g. What are the skills of the applicant?",
    height=100
)

# ─── Filters ────────────────────────────────────────────────────────────────

st.subheader("🔧 Filters (Optional)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    filter_language = st.selectbox(
        "Language",
        ["Any", "english", "bangla", "mixed"]
    )

with col2:
    filter_doc_type = st.selectbox(
        "Document Type",
        ["Any", "general", "letter", "cv", "report", "invoice", "form", "other"]
    )

with col3:
    filter_date_enabled = st.checkbox("Filter by Date")
    filter_date = st.date_input(
        "Date", key="filter_date") if filter_date_enabled else None

with col4:
    top_k = st.slider("Top K Chunks", min_value=1, max_value=10, value=5)

search_btn = st.button("🔍 Search", use_container_width=True)

# ─── Run Query ──────────────────────────────────────────────────────────────

if search_btn:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching and generating answer..."):
            payload = {
                "query": query,
                "top_k": top_k,
                "language": None if filter_language == "Any" else filter_language,
                "doc_type": None if filter_doc_type == "Any" else filter_doc_type,
                "doc_date": str(filter_date) if filter_date_enabled and filter_date else None
            }

            response = requests.post(f"{API_URL}/query", json=payload)
            result = response.json()

        # ─── Answer ─────────────────────────────────────────────────────────
        st.subheader("🤖 Answer")
        st.success(result["answer"])

        # ─── Sources ────────────────────────────────────────────────────────
        if result["sources"]:
            st.subheader("📚 Sources")
            for i, source in enumerate(result["sources"]):
                with st.expander(f"Source {i+1} — {source['filename']} (score: {source['relevance_score']})"):
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Language", source["language"])
                    col_b.metric("Type", source["doc_type"])
                    col_c.metric("Date", source["doc_date"] or "N/A")
                    col_d.metric("Relevance", source["relevance_score"])
