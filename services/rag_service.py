"""
RAG Service — Retrieval Augmented Generation
Indexes course documents in ChromaDB or a JSON/TF-IDF Fallback Vector Store.
"""
import os
import json
import math
from typing import List, Optional
from config import settings

# ─── Fallback JSON Vector Store Implementation ──────────
FALLBACK_CACHE_PATH = os.path.join("static", "uploads", "notes", "rag_cache.json")

def load_fallback_cache() -> dict:
    """Load the fallback RAG JSON cache"""
    os.makedirs(os.path.dirname(FALLBACK_CACHE_PATH), exist_ok=True)
    if not os.path.exists(FALLBACK_CACHE_PATH):
        return {}
    try:
        with open(FALLBACK_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading RAG fallback cache: {e}")
        return {}

def save_fallback_cache(data: dict):
    """Save the fallback RAG JSON cache"""
    try:
        with open(FALLBACK_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving RAG fallback cache: {e}")

# ─── Embedding & Client loaders (Safe Imports) ──────────
def get_embedding_function():
    """Get embedding function for ChromaDB"""
    try:
        from chromadb.utils import embedding_functions
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
    except Exception:
        return None

def get_chroma_client():
    """Get ChromaDB client"""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        return client
    except Exception:
        return None

def get_collection(course_id: str):
    """Get or create ChromaDB collection for a course"""
    client = get_chroma_client()
    if not client:
        return None
    
    ef = get_embedding_function()
    try:
        collection = client.get_or_create_collection(
            name = f"course_{course_id.replace('-', '_')}",
            embedding_function = ef,
            metadata = {"course_id": course_id}
        )
        return collection
    except Exception:
        return None

# ─── File Text Parsers ──────────────────────────────────
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """Split text into overlapping chunks"""
    chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
    overlap    = overlap    or settings.RAG_CHUNK_OVERLAP
    
    words  = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]

# ─── Public APIs with Fallback Capability ──────────────
def index_document(
    note_id:   str,
    file_path: str,
    course_id: str,
    db = None
) -> bool:
    """Index a document into ChromaDB (or JSON fallback) for RAG"""
    # 1. Extract text from note file
    try:
        ext = file_path.split(".")[-1].lower()
        if ext == "pdf":
            text = extract_text_from_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        
        if not text.strip():
            return False
        
        chunks = chunk_text(text)
        if not chunks:
            return False
    except Exception as e:
        print(f"Error parsing document {file_path}: {e}")
        return False

    # 2. Try ChromaDB indexing
    collection = get_collection(course_id)
    if collection:
        try:
            ids       = [f"{note_id}_{i}" for i in range(len(chunks))]
            metadatas = [{"note_id": note_id, "course_id": course_id, "chunk_index": i} for i in range(len(chunks))]
            collection.add(documents=chunks, ids=ids, metadatas=metadatas)
            
            # Update SQLite models
            if db:
                import models
                note = db.query(models.LectureNote).filter(models.LectureNote.id == note_id).first()
                if note:
                    note.is_indexed = True
                    note.vector_ids = ids
                    db.commit()
            return True
        except Exception as e:
            print(f"ChromaDB indexing failed, falling back to JSON: {e}")

    # 3. Fallback JSON Indexing
    try:
        cache = load_fallback_cache()
        if course_id not in cache:
            cache[course_id] = []
        
        # Remove existing chunks for this note to prevent duplicates
        cache[course_id] = [c for c in cache[course_id] if c.get("note_id") != note_id]
        
        # Append new chunks
        ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{note_id}_{i}"
            ids.append(chunk_id)
            cache[course_id].append({
                "id":          chunk_id,
                "note_id":     note_id,
                "content":     chunk,
                "chunk_index": i
            })
        
        save_fallback_cache(cache)

        # Update SQLite models
        if db:
            import models
            note = db.query(models.LectureNote).filter(models.LectureNote.id == note_id).first()
            if note:
                note.is_indexed = True
                note.vector_ids = ids
                db.commit()
                
        print(f"Fallback Indexed {len(chunks)} chunks for note {note_id}")
        return True
    except Exception as e:
        print(f"Fallback indexing error: {e}")
        return False

def search_course_context(
    query:     str,
    course_id: str,
    top_k:     int = None
) -> List[dict]:
    """Search indexed documents for relevant context (using ChromaDB or Fallback TF-IDF)"""
    top_k = top_k or settings.RAG_TOP_K
    
    # 1. Try ChromaDB Search
    collection = get_collection(course_id)
    if collection:
        try:
            results = collection.query(
                query_texts = [query],
                n_results   = top_k,
                where       = {"course_id": course_id}
            )
            if results and results.get("documents") and len(results["documents"][0]) > 0:
                docs = []
                for i, doc in enumerate(results["documents"][0]):
                    docs.append({
                        "content":  doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    })
                return docs
        except Exception as e:
            print(f"ChromaDB search failed, falling back to keyword search: {e}")

    # 2. Fallback Search (TF-IDF / Word overlap score)
    try:
        cache = load_fallback_cache()
        chunks = cache.get(course_id, [])
        if not chunks:
            return []

        # Simple term-matching TF-IDF ranking in pure Python
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for c in chunks:
            content = c["content"].lower()
            # Calculate match score (word overlap + simple term frequency weight)
            score = 0
            for qw in query_words:
                count = content.count(qw)
                if count > 0:
                    score += (1 + math.log(count)) * (1.0 / (1.0 + math.log(len(content.split()))))
            
            if score > 0:
                scored_chunks.append((score, c))
        
        # Sort desc by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Format output
        results = []
        for score, c in scored_chunks[:top_k]:
            results.append({
                "content":  c["content"],
                "metadata": {"note_id": c["note_id"], "course_id": course_id, "chunk_index": c["chunk_index"]},
                "distance": float(score)  # Use score as weight
            })
        return results
    except Exception as e:
        print(f"Fallback search error: {e}")
        return []

def delete_course_index(course_id: str) -> bool:
    """Delete all indexed documents for a course"""
    # 1. Try ChromaDB Delete
    client = get_chroma_client()
    if client:
        try:
            client.delete_collection(f"course_{course_id.replace('-', '_')}")
        except Exception:
            pass

    # 2. Fallback Delete
    try:
        cache = load_fallback_cache()
        if course_id in cache:
            del cache[course_id]
            save_fallback_cache(cache)
        return True
    except Exception as e:
        print(f"Fallback delete collection error: {e}")
        return False

def get_index_stats(course_id: str) -> dict:
    """Get indexing statistics for a course"""
    # 1. Try ChromaDB stats
    collection = get_collection(course_id)
    if collection:
        try:
            count = collection.count()
            return {"total_chunks": count, "indexed": count > 0}
        except:
            pass

    # 2. Fallback stats
    try:
        cache = load_fallback_cache()
        count = len(cache.get(course_id, []))
        return {"total_chunks": count, "indexed": count > 0}
    except:
        return {"total_chunks": 0, "indexed": False}
