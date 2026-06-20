import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from ocr import run_ocr
from pipeline import store_document
from rag import rag_query

app = FastAPI(title="Local OCR & RAG System")

# Allow Streamlit frontend to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── Request/Response Models ───────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    language: Optional[str] = None
    doc_type: Optional[str] = None
    doc_date: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list


# ─── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "OCR RAG System is running"}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="general"),
    doc_date: Optional[str] = Form(default=None)
):
    """
    Upload a scanned PDF or image.
    Runs OCR locally, chunks, embeds, and stores in ChromaDB.
    """
    # Save uploaded file to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Run OCR
        extracted_text = run_ocr(file_path)

        if not extracted_text.strip():
            return {"error": "OCR extracted no text from this file. Try a clearer scan."}

        if doc_date == "string" or doc_date == "":
            doc_date = None

        # Store in ChromaDB
        result = store_document(
            text=extracted_text,
            filename=file.filename,
            doc_type=doc_type,
            doc_date=doc_date
        )

        return {
            "message": "Document processed successfully",
            "filename": result["filename"],
            "language": result["language"],
            "total_chunks": result["total_chunks"],
            "doc_type": result["doc_type"],
            "doc_date": result["doc_date"]
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """
    Ask a natural language question over uploaded documents.
    Optionally filter by language, doc_type, or doc_date.
    """
    result = rag_query(
        query=request.query,
        top_k=request.top_k,
        language=request.language,
        doc_type=request.doc_type,
        doc_date=request.doc_date
    )
    return result


@app.get("/documents")
def list_documents():
    """List all unique documents stored in ChromaDB."""
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("documents")

    results = collection.get(include=["metadatas"])

    # Deduplicate by filename
    seen = {}
    for meta in results["metadatas"]:
        fname = meta["filename"]
        if fname not in seen:
            seen[fname] = {
                "filename": fname,
                "language": meta["language"],
                "doc_type": meta["doc_type"],
                "doc_date": meta["doc_date"]
            }

    return {"documents": list(seen.values())}
