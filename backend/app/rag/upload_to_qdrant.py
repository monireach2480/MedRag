"""
Upload locally saved embeddings to Qdrant Cloud
Usage: python -m app.rag.upload_to_qdrant
"""

import sys
import os
from pathlib import Path
from typing import List, Dict
import json
import pickle

# Add your Qdrant Cloud credentials here (DELETE AFTER USE)
# These will override .env file settings for this session

# Force use cloud (set to False to use local)
USE_QDRANT_CLOUD = True

# Local cache directory
LOCAL_CACHE_DIR = Path("data/embeddings_cache")
LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_qdrant_client():
    """Get Qdrant client - prioritizes cloud if credentials provided"""
    
    # First check if cloud credentials are set in this script
    if USE_QDRANT_CLOUD and QDRANT_CLOUD_URL != "https://your-cluster-url.gcp.qdrant.io:6333":
        if QDRANT_CLOUD_API_KEY != "your-api-key-here":
            print(f"  ☁️  Connecting to Qdrant Cloud: {QDRANT_CLOUD_URL}")
            from qdrant_client import QdrantClient
            return QdrantClient(
                url=QDRANT_CLOUD_URL,
                api_key=QDRANT_CLOUD_API_KEY,
                timeout=120,
            )
    
    # Try from environment variables
    from app.core.config import settings
    if settings.QDRANT_URL and settings.QDRANT_API_KEY:
        print(f"  ☁️  Connecting to Qdrant Cloud from env: {settings.QDRANT_URL}")
        from qdrant_client import QdrantClient
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=120,
        )
    
    # Fallback to local
    print(f"  🔌 Connecting to local Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    from qdrant_client import QdrantClient
    from app.core.config import settings
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )


def list_local_embeddings() -> List[Path]:
    """List all locally saved embedding files"""
    json_files = list(LOCAL_CACHE_DIR.glob("*.json"))
    # Sort by creation time (newest first)
    return sorted(json_files, key=lambda x: x.stat().st_ctime, reverse=True)


def load_local_embeddings(filepath: Path) -> Dict:
    """Load locally saved embeddings"""
    print(f"  📂 Loading: {filepath.name}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"     Found {data['total_chunks']} chunks from {data['source_file']}")
    return data


def ensure_collection(client, collection_name: str = "medical_docs"):
    """Ensure collection exists in Qdrant"""
    from qdrant_client.models import VectorParams, Distance
    
    collections = client.get_collections().collections
    existing_names = [c.name for c in collections]
    
    if collection_name not in existing_names:
        print(f"  📚 Creating collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,  # BAAI/bge-small-en-v1.5 dimension
                distance=Distance.COSINE,
            ),
        )
    else:
        print(f"  ✅ Collection '{collection_name}' already exists")


def upload_to_qdrant(filepath: Path = None, batch_size: int = 25, collection: str = "medical_docs"):
    """Upload embeddings to Qdrant Cloud"""
    
    # Get Qdrant client
    client = get_qdrant_client()
    
    # Get files to upload
    if filepath:
        files = [filepath]
    else:
        files = list_local_embeddings()
    
    if not files:
        print("❌ No local embedding files found. Run ingestion first:")
        print("   python -m app.rag.ingest docs/Medical_book.pdf")
        return
    
    print(f"\n📁 Found {len(files)} local embedding file(s)\n")
    
    # Ensure collection exists
    ensure_collection(client, collection)
    
    total_uploaded = 0
    
    for filepath in files:
        print(f"\n{'='*50}")
        print(f"Processing: {filepath.name}")
        print(f"{'='*50}")
        
        # Load data
        data = load_local_embeddings(filepath)
        chunks = data["chunks"]
        
        # Prepare points for Qdrant
        points = []
        for chunk in chunks:
            from qdrant_client.models import PointStruct
            
            point = PointStruct(
                id=chunk["id"],  # Use the existing UUID
                vector=chunk["vector"],
                payload={
                    "text": chunk["text"],
                    "filename": chunk["filename"],
                    "page": chunk["page"],
                    "section": chunk.get("section", ""),
                    "chunk_index": chunk.get("chunk_index", 0),
                }
            )
            points.append(point)
        
        # Upload in batches
        total_batches = (len(points) + batch_size - 1) // batch_size
        print(f"\n  ☁️  Uploading {len(points)} chunks to Qdrant Cloud...")
        print(f"     Batch size: {batch_size}, Total batches: {total_batches}")
        
        success_count = 0
        failed_batches = []
        
        for i in range(0, len(points), batch_size):
            batch_num = (i // batch_size) + 1
            batch = points[i:i + batch_size]
            
            try:
                client.upsert(
                    collection_name=collection,
                    points=batch,
                    wait=True,
                )
                success_count += len(batch)
                print(f"     ✓ Batch {batch_num}/{total_batches} uploaded ({len(batch)} chunks)")
                
            except Exception as e:
                print(f"     ✗ Batch {batch_num}/{total_batches} failed: {str(e)[:100]}")
                failed_batches.append((batch_num, batch))
                
                # Try with smaller batch size for failed batch
                if len(batch) > 5:
                    print(f"     🔄 Retrying batch {batch_num} in smaller chunks (5 each)...")
                    for j in range(0, len(batch), 5):
                        sub_batch = batch[j:j+5]
                        try:
                            client.upsert(
                                collection_name=collection,
                                points=sub_batch,
                                wait=True,
                            )
                            success_count += len(sub_batch)
                            print(f"        ✓ Sub-batch {j//5 + 1}/{(len(batch)-1)//5 + 1} uploaded")
                        except Exception as sub_e:
                            print(f"        ✗ Sub-batch failed: {str(sub_e)[:80]}")
        
        print(f"\n  📊 Upload summary for {data['source_file']}:")
        print(f"     ✅ Successfully uploaded: {success_count}/{len(points)} chunks")
        
        if success_count != len(points):
            print(f"     ⚠️  Failed: {len(points) - success_count} chunks")
            print(f"     💡 Try: python -m app.rag.upload_to_qdrant --batch-size 10")
        
        total_uploaded += success_count
    
    print(f"\n{'='*50}")
    print(f"🎉 TOTAL UPLOADED: {total_uploaded} chunks to Qdrant Cloud")
    print(f"{'='*50}\n")
    
    return total_uploaded


def check_collection_stats(collection: str = "medical_docs"):
    """Check how many points are in the collection"""
    client = get_qdrant_client()
    
    try:
        collection_info = client.get_collection(collection)
        points_count = collection_info.points_count
        print(f"\n📊 Collection '{collection}' stats:")
        print(f"   Total points: {points_count}")
        print(f"   Vectors count: {collection_info.vectors_count}")
        print(f"   Status: {collection_info.status}\n")
        return points_count
    except Exception as e:
        print(f"❌ Error getting collection info: {e}")
        return 0


def delete_collection(collection: str = "medical_docs"):
    """Delete entire collection (use with caution)"""
    confirm = input(f"⚠️  Delete entire collection '{collection}'? Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        client = get_qdrant_client()
        client.delete_collection(collection)
        print(f"✅ Collection '{collection}' deleted")
    else:
        print("Cancelled")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload local embeddings to Qdrant Cloud")
    parser.add_argument("--file", type=Path, help="Specific JSON file to upload")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size for upload (default: 25)")
    parser.add_argument("--collection", type=str, default="medical_docs", help="Collection name")
    parser.add_argument("--check", action="store_true", help="Check collection stats")
    parser.add_argument("--delete-collection", action="store_true", help="Delete collection (CAUTION)")
    
    args = parser.parse_args()
    
    if args.check:
        check_collection_stats(args.collection)
    elif args.delete_collection:
        delete_collection(args.collection)
    else:
        upload_to_qdrant(
            filepath=args.file,
            batch_size=args.batch_size,
            collection=args.collection
        )


if __name__ == "__main__":
    main()