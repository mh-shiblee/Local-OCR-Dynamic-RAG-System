import chromadb
from langdetect import detect
from sentence_transformers import SentenceTransformer
from datetime import datetime
import hashlib

# Load embedding model once at startup
# Multilingual model — handles Bangla + English
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ChromaDB local persistent storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="documents")


def detect_language(text: str) -> str:
    """Detect if text is Bangla, English, or mixed."""
    try:
        sample = text[:500]  # use first 500 chars for detection
        lang = detect(sample)
        if lang == "bn":
            return "bangla"
        elif lang == "en":
            return "english"
        else:
            return "mixed"
    except:
        return "unknown"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # overlap keeps context between chunks

    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert list of text chunks into embeddings."""
    return embedding_model.encode(texts).tolist()


def store_document(
    text: str,
    filename: str,
    doc_type: str = "general",
    doc_date: str = None
) -> dict:
    """
    Full pipeline: chunk → embed → store in ChromaDB.
    Returns a summary of what was stored.
    """

    if doc_date is None:
        doc_date = datetime.today().strftime("%Y-%m-%d")

    language = detect_language(text)
    chunks = chunk_text(text)
    embeddings = embed_texts(chunks)

    # Build unique ID for each chunk using filename + index
    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        # Unique ID: hash of filename + chunk index
        unique_id = hashlib.md5(f"{filename}_{i}".encode()).hexdigest()
        ids.append(unique_id)
        metadatas.append({
            "filename": filename,
            "chunk_index": i,
            "language": language,
            "doc_type": doc_type,
            "doc_date": doc_date,
        })

    # Store in ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )

    return {
        "filename": filename,
        "language": language,
        "total_chunks": len(chunks),
        "doc_date": doc_date,
        "doc_type": doc_type
    }
