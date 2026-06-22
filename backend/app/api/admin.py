import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.core.deps import get_current_user
from app.rag.ingest import ingest_pdf
from app.rag.retriever import _get_client
from app.core.config import settings
from app.api.schemas import UploadResponse, DocumentInfo

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ── Upload PDF ────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(_require_admin),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    # Save to a temp file then ingest
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        # Rename tmp file so Qdrant payload stores the real filename
        named_path = tmp_path.parent / file.filename
        tmp_path.rename(named_path)
        chunks_inserted = ingest_pdf(named_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(exc)}",
        )
    finally:
        # Cleanup
        if named_path.exists():
            named_path.unlink(missing_ok=True)

    return UploadResponse(
        filename=file.filename,
        chunks_inserted=chunks_inserted,
        message=f"Successfully ingested {chunks_inserted} chunks from {file.filename}",
    )


# ── List documents ────────────────────────────────────────────────────────────

@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(current_user: User = Depends(_require_admin)):
    """
    Returns unique filenames and chunk counts from Qdrant.
    Uses scroll to aggregate payload metadata.
    """
    client = _get_client()
    try:
        # Scroll through all points and aggregate by filename
        filename_counts: dict[str, int] = {}
        offset = None

        while True:
            results, next_offset = client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in results:
                fname = (point.payload or {}).get("filename", "unknown")
                filename_counts[fname] = filename_counts.get(fname, 0) + 1

            if next_offset is None:
                break
            offset = next_offset

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Qdrant error: {str(exc)}",
        )

    return [DocumentInfo(filename=fname, chunks=count) for fname, count in sorted(filename_counts.items())]


# ── Delete document ───────────────────────────────────────────────────────────

@router.delete("/documents/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    filename: str,
    current_user: User = Depends(_require_admin),
):
    """Delete all Qdrant points where payload.filename matches."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()
    try:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Qdrant delete error: {str(exc)}",
        )
