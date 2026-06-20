# 🔍 Local OCR & Dynamic RAG System

A fully localized, privacy-preserving document processing pipeline with multilingual OCR (Bangla + English) and a Retrieval-Augmented Generation (RAG) search engine — no external APIs, no data leaves your machine.

> Built as a Technical Assessment submission.

---

## 📁 Project Structure

```
ocr-rag-system/
├── backend/
│   ├── main.py          # FastAPI app — upload & query endpoints
│   ├── ocr.py           # Surya OCR — local text extraction
│   ├── pipeline.py      # Chunking, embedding, ChromaDB storage
│   ├── rag.py           # Semantic search + Ollama LLM generation
│   └── uploads/         # Uploaded files saved here
├── frontend/
│   └── app.py           # Streamlit UI
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.11
- [Ollama](https://ollama.com) installed locally

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ocr-rag-system.git
cd ocr-rag-system
```

### 2. Create Virtual Environment (Python 3.11)

```bash
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> Note: transformers is pinned to 4.44.0 for compatibility with surya-ocr 0.6.0.
> Do not upgrade it.

### 4. Pull the Local LLM

```bash
ollama pull llama3.2
```

---

## Running the System

You need **three terminals** running simultaneously:

**Terminal 1 — Ollama**

```bash
ollama serve
```

**Terminal 2 — FastAPI Backend**

```bash
cd backend
uvicorn main:app --reload
```

**Terminal 3 — Streamlit Frontend**

```bash
cd frontend
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

USER UPLOADS A FILE
        │
        ▼
┌─────────────────────┐
│   Streamlit UI      │  User picks PDF + doc_type + date
│   frontend/app.py   │  Clicks "Upload & Process"
└────────┬────────────┘
         │ HTTP POST /upload
         ▼
┌─────────────────────┐
│   FastAPI           │  Receives file, saves to uploads/
│   backend/main.py   │  
└────────┬────────────┘
         │ calls run_ocr()
         ▼
┌─────────────────────┐
│   Surya OCR         │  Converts PDF pages → images
│   backend/ocr.py    │  Reads pixels → extracts text
└────────┬────────────┘
         │ returns raw text string
         ▼
┌─────────────────────┐
│   Pipeline          │  1. Detects language (Bangla/English/Mixed)
│   backend/          │  2. Splits text into 500-word chunks
│   pipeline.py       │  3. Embeds each chunk into a vector (384 numbers)
│                     │  4. Stores vectors + metadata in ChromaDB
└────────┬────────────┘
         │ returns summary
         ▼
┌─────────────────────┐
│   ChromaDB          │  Persists everything to chroma_db/ folder
│   chroma_db/        │  Each chunk stored with:
│                     │  - vector embedding
│                     │  - original text
│                     │  - filename, language, doc_type, doc_date
└─────────────────────┘


USER ASKS A QUESTION
        │
        ▼
┌─────────────────────┐
│   Streamlit UI      │  User types question
│   frontend/app.py   │  Optionally sets filters (language, type, date)
│                     │  Clicks "Search"
└────────┬────────────┘
         │ HTTP POST /query
         ▼
┌─────────────────────┐
│   FastAPI           │  Receives query + filters
│   backend/main.py   │  Passes to rag_query()
└────────┬────────────┘
         │ calls retrieve_chunks()
         ▼
┌─────────────────────┐
│   RAG - Retrieval   │  1. Embeds the user query into a vector
│   backend/rag.py    │  2. Builds metadata filter if user set any
│                     │  3. ChromaDB finds top-K most similar chunks
│                     │     (compares query vector vs stored vectors)
│                     │  4. Returns most relevant chunks + scores
└────────┬────────────┘
         │ chunks passed to build_prompt()
         ▼
┌─────────────────────┐
│   RAG - Generation  │  Builds prompt:
│   backend/rag.py    │  "Answer based on this context: [chunks]
│                     │   Question: [user query]"
└────────┬────────────┘
         │ sends prompt to Ollama
         ▼
┌─────────────────────┐
│   Ollama (llama3.2) │  Local LLM reads the context + question
│   runs locally      │  Generates a grounded answer
│   port 11434        │  Never makes anything up beyond the context
└────────┬────────────┘
         │ returns answer text
         ▼
┌─────────────────────┐
│   Streamlit UI      │  Displays answer
│   frontend/app.py   │  Shows source documents + relevance scores
└─────────────────────┘


## 🛠️ Tech Stack

| Layer      | Tool                                    |
| ---------- | --------------------------------------- |
| OCR        | Surya 0.6.0                             |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| Vector DB  | ChromaDB (persistent, file-based)       |
| Local LLM  | Ollama — llama3.2                       |
| Backend    | FastAPI                                 |
| Frontend   | Streamlit                               |
