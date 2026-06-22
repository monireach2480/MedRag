"""Local storage for embeddings before uploading to Qdrant"""
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict

LOCAL_CACHE_DIR = Path("data/embeddings_cache")
LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def save_embeddings_locally(chunks: List[Dict], vectors: List[List[float]], filename: str) -> Path:
    """Save chunks and their embeddings to local disk"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = Path(filename).stem.replace(" ", "_")
    
    # Save as JSON (human readable, but larger)
    data = {
        "source_file": filename,
        "timestamp": timestamp,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "id": c["id"],
                "text": c["text"],
                "filename": c["filename"],
                "page": c["page"],
                "section": c["section"],
                "chunk_index": c["chunk_index"],
                "vector": v.tolist() if hasattr(v, 'tolist') else v
            }
            for c, v in zip(chunks, vectors)
        ]
    }
    
    json_path = LOCAL_CACHE_DIR / f"{safe_filename}_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    # Also save as pickle for faster loading (binary format)
    pickle_path = LOCAL_CACHE_DIR / f"{safe_filename}_{timestamp}.pkl"
    with open(pickle_path, "wb") as f:
        pickle.dump(data, f)
    
    print(f"  💾 Saved locally to: {json_path}")
    print(f"  💾 Pickle saved to: {pickle_path}")
    
    return json_path

def load_local_embeddings(filepath: Path) -> Dict:
    """Load locally saved embeddings"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def list_local_embeddings() -> List[Path]:
    """List all locally saved embedding files"""
    return list(LOCAL_CACHE_DIR.glob("*.json"))

def delete_local_embeddings(filename_pattern: str = None):
    """Delete local embedding files"""
    if filename_pattern:
        for f in LOCAL_CACHE_DIR.glob(f"*{filename_pattern}*"):
            f.unlink()
            print(f"  🗑 Deleted: {f}")
    else:
        for f in LOCAL_CACHE_DIR.glob("*.json"):
            f.unlink()
        for f in LOCAL_CACHE_DIR.glob("*.pkl"):
            f.unlink()