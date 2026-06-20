import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json

# Same embedding model as pipeline.py — must match
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ChromaDB connection
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="documents")


def embed_query(query: str) -> list[float]:
    """Embed the user query using the same model used during ingestion."""
    return embedding_model.encode(query).tolist()


def build_metadata_filter(
    language: str = None,
    doc_type: str = None,
    doc_date: str = None
) -> dict | None:
    """
    Build ChromaDB where filter from user-provided metadata.
    Only includes fields the user actually specified.
    """
    conditions = []

    if language:
        conditions.append({"language": {"$eq": language}})
    if doc_type:
        conditions.append({"doc_type": {"$eq": doc_type}})
    if doc_date:
        conditions.append({"doc_date": {"$eq": doc_date}})

    if len(conditions) == 0:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    language: str = None,
    doc_type: str = None,
    doc_date: str = None
) -> list[dict]:
    """
    Semantic search over ChromaDB with optional metadata filters.
    Returns top_k most relevant chunks with their metadata.
    """
    query_embedding = embed_query(query)
    where_filter = build_metadata_filter(language, doc_type, doc_date)

    search_params = {
        "query_embeddings": [query_embedding],
        # avoid requesting more than stored
        "n_results": min(top_k, collection.count()),
        "include": ["documents", "metadatas", "distances"]
    }

    if where_filter:
        search_params["where"] = where_filter

    results = collection.query(**search_params)

    # Format results into clean list of dicts
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            # convert distance to similarity
            "score": round(1 / (1 + results["distances"][0][i]), 4)
        })

    return chunks


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Build the RAG prompt combining retrieved context + user query."""
    context = ""
    for i, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        context += f"\n[Chunk {i+1} | File: {meta['filename']} | Lang: {meta['language']} | Date: {meta['doc_date']}]\n"
        context += chunk["text"] + "\n"

    prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the context provided below.
If the answer is not found in the context, say "I could not find this information in the uploaded documents."
Do not make up information.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""

    return prompt


def ask_ollama(prompt: str, model: str = "llama3.2") -> str:
    """Send prompt to local Ollama and return the response."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"].strip()


def rag_query(
    query: str,
    top_k: int = 5,
    language: str = None,
    doc_type: str = None,
    doc_date: str = None
) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks (with optional filters)
    2. Build prompt with context
    3. Send to Ollama
    4. Return answer + source chunks
    """
    chunks = retrieve_chunks(query, top_k, language, doc_type, doc_date)

    if not chunks:
        return {
            "answer": "No relevant documents found. Try uploading documents first or adjusting your filters.",
            "sources": []
        }

    prompt = build_prompt(query, chunks)
    answer = ask_ollama(prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "filename": c["metadata"]["filename"],
                "language": c["metadata"]["language"],
                "doc_type": c["metadata"]["doc_type"],
                "doc_date": c["metadata"]["doc_date"],
                "relevance_score": c["score"]
            }
            for c in chunks
        ]
    }
