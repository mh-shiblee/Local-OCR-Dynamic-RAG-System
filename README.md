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

## 🔗 Links

- **Demo Video:** `YOUR_YOUTUBE_LINK_HERE`

---

## 🛠️ Tech Stack

| Layer      | Tool                                    |
| ---------- | --------------------------------------- |
| OCR        | Surya 0.6.0                             |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| Vector DB  | ChromaDB (persistent, file-based)       |
| Local LLM  | Ollama — llama3.2                       |
| Backend    | FastAPI                                 |
| Frontend   | Streamlit                               |
