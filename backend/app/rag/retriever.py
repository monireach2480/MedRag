from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)
from app.core.config import settings
from app.rag.embedder import embed_query  # use query prefix for searches


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    filename: str
    page: int
    score: float
    section: str = ""  # section heading if extracted


def _get_client() -> QdrantClient:
    if settings.QDRANT_URL:
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def ensure_collection() -> None:
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.EMBED_DIMENSION,
                distance=Distance.COSINE,
            ),
        )


def upsert_chunks(points: list[dict]) -> None:
    client = _get_client()
    ensure_collection()

    qdrant_points = [
        PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload={
                "text": p["text"],
                "filename": p["filename"],
                "page": p["page"],
                "section": p.get("section", ""),
                "chunk_index": p.get("chunk_index", 0),
            },
        )
        for p in points
    ]
    
    # Upsert in batches with timeout handling
    batch_size = 50  # Reduced from 100 to avoid timeouts
    total_batches = (len(qdrant_points) + batch_size - 1) // batch_size
    
    print(f"  📤 Uploading {len(qdrant_points)} chunks in {total_batches} batches...")
    
    for i in range(0, len(qdrant_points), batch_size):
        batch_num = (i // batch_size) + 1
        batch = qdrant_points[i:i + batch_size]
        
        try:
            client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=batch,
                timeout=120,  # 2 minutes timeout per batch
                wait=True
            )
            print(f"    ✓ Batch {batch_num}/{total_batches} uploaded ({len(batch)} chunks)")
        except Exception as e:
            print(f"    ✗ Batch {batch_num}/{total_batches} failed: {e}")
            # Try one more time with smaller batch
            if len(batch) > 10:
                print(f"    🔄 Retrying batch {batch_num} in smaller chunks...")
                for j in range(0, len(batch), 10):
                    sub_batch = batch[j:j+10]
                    client.upsert(
                        collection_name=settings.QDRANT_COLLECTION,
                        points=sub_batch,
                        timeout=60,
                        wait=True
                    )
            else:
                raise
    
    print(f"  ✅ Successfully uploaded all {len(qdrant_points)} chunks")


def search(query: str, top_k: int = None) -> list[RetrievedChunk]:
    """
    Embed query with BGE prefix and return top-K chunks above score threshold.
    """
    k = top_k or settings.TOP_K_RESULTS
    client = _get_client()

    query_vector = embed_query(query)  # uses BGE prefix

    results: list[ScoredPoint] = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=k,
        with_payload=True,
        score_threshold=settings.SCORE_THRESHOLD,
    )

    chunks = []
    for r in results:
        payload = r.payload or {}
        chunks.append(
            RetrievedChunk(
                chunk_id=str(r.id),
                text=payload.get("text", ""),
                filename=payload.get("filename", "unknown"),
                page=payload.get("page", 0),
                score=r.score,
                section=payload.get("section", ""),
            )
        )
    return chunks


def delete_by_filename(filename: str) -> None:
    """Delete all chunks belonging to a specific document."""
    client = _get_client()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
        ),
    )
