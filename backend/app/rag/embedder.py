from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# bge-small uses a query prefix for better retrieval accuracy
# This is specific to the BGE model family
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load once, cache for process lifetime."""
    return SentenceTransformer(settings.EMBED_MODEL)


def embed_query(query: str) -> list[float]:
    """
    Embed a user query.
    BGE models perform better with a prefix on the query side only.
    Documents are embedded WITHOUT the prefix during ingestion.
    """
    model = _load_model()
    prefixed = BGE_QUERY_PREFIX + query
    vector = model.encode(prefixed, normalize_embeddings=True)
    return vector.tolist()


def embed_text(text: str) -> list[float]:
    """Embed a single document chunk (no prefix)."""
    model = _load_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple document chunks efficiently (no prefix)."""
    model = _load_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )
    return [v.tolist() for v in vectors]
