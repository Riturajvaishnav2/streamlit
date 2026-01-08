import uuid
from typing import Any, Dict, List, Optional

from langchain_openai.embeddings import OpenAIEmbeddings

from src.core.config import QDRANT_COLLECTION, QDRANT_TOP_K
from src.core.state import _now_iso


# Create a Qdrant client if configured.
def _get_qdrant_client() -> Optional[Any]:
    import os

    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    if not qdrant_url:
        return None
    try:
        from qdrant_client import QdrantClient
    except Exception:
        return None
    api_key = os.getenv("QDRANT_API_KEY", "").strip() or None
    return QdrantClient(url=qdrant_url, api_key=api_key)


# Report Qdrant connection status and collections.
def _qdrant_status() -> Dict[str, Any]:
    import os

    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    if not qdrant_url:
        return {"available": False, "error": "QDRANT_URL is not set."}
    client = _get_qdrant_client()
    if not client:
        return {"available": False, "error": "Qdrant client could not be created."}
    try:
        collections = client.get_collections().collections
    except Exception as exc:
        return {"available": False, "error": str(exc), "url": qdrant_url}
    names = [c.name for c in collections]
    return {"available": True, "url": qdrant_url, "collections": names}


# Inspect a Qdrant collection vector size.
def _collection_vector_size(client: Any, name: str) -> Optional[int]:
    try:
        info = client.get_collection(name)
    except Exception:
        return None
    config = getattr(info, "config", None)
    params = getattr(config, "params", None)
    vectors = getattr(params, "vectors", None)
    size = getattr(vectors, "size", None)
    if isinstance(size, int):
        return size
    return None


# Ensure a Qdrant collection exists with the target vector size.
def _ensure_qdrant_collection(client: Any, name: str, vector_size: int) -> None:
    try:
        from qdrant_client.http.models import Distance, VectorParams
    except Exception:
        return
    existing = client.get_collections().collections
    if any(c.name == name for c in existing):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


# Choose the appropriate collection based on vector size.
def _resolve_qdrant_collection(client: Any, vector_size: int) -> str:
    existing = client.get_collections().collections
    if any(c.name == QDRANT_COLLECTION for c in existing):
        existing_size = _collection_vector_size(client, QDRANT_COLLECTION)
        if existing_size == vector_size:
            return QDRANT_COLLECTION
        return f"{QDRANT_COLLECTION}_{vector_size}"
    return QDRANT_COLLECTION


# Store prompt/response snippets in Qdrant for history.
def _qdrant_upsert_history(
    provider: str,
    api_key: str,
    agreement_key: str,
    prompt_version: str,
    role: str,
    content: str,
    base_url: str = "",
    model_name: str = "",
) -> None:
    client = _get_qdrant_client()
    if not client:
        return
    provider_key = provider.strip().lower()
    if provider_key in {"local", "ollama"}:
        try:
            from langchain_ollama import OllamaEmbeddings
        except Exception:
            return
        ollama_base_url = base_url.strip() or "http://localhost:11434"
        embeddings = OllamaEmbeddings(model=model_name or "llama3.2", base_url=ollama_base_url)
    else:
        if not api_key:
            import os

            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return
        embeddings = OpenAIEmbeddings(api_key=api_key)
    vector = embeddings.embed_query(content)
    collection_name = _resolve_qdrant_collection(client, len(vector))
    _ensure_qdrant_collection(client, collection_name, len(vector))
    point = {
        "id": str(uuid.uuid4()),
        "vector": vector,
        "payload": {
            "agreement_key": agreement_key,
            "prompt_version": prompt_version,
            "role": role,
            "content": content,
            "created_at": _now_iso(),
        },
    }
    client.upsert(collection_name=collection_name, points=[point])


# Fetch stored history for a specific agreement key.
def _qdrant_fetch_history(agreement_key: str, limit: int = QDRANT_TOP_K) -> List[Dict[str, Any]]:
    client = _get_qdrant_client()
    if not client:
        return []
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    except Exception:
        return []
    existing = client.get_collections().collections
    collection_names = [
        c.name
        for c in existing
        if c.name == QDRANT_COLLECTION or c.name.startswith(f"{QDRANT_COLLECTION}_")
    ]
    if not collection_names:
        return []
    scroll_filter = Filter(
        must=[FieldCondition(key="agreement_key", match=MatchValue(value=agreement_key))]
    )
    payloads: List[Dict[str, Any]] = []
    for name in collection_names:
        points, _ = client.scroll(
            collection_name=name,
            limit=limit,
            scroll_filter=scroll_filter,
            with_payload=True,
            with_vectors=False,
        )
        payloads.extend([p.payload for p in points if p.payload])
    payloads.sort(key=lambda item: item.get("created_at", ""))
    return payloads
