    """
    Medical PDF ingestion pipeline — optimized for clinical documents.

    Strategy:
    1. Extract text per page with pypdf
    2. Clean: remove headers/footers, fix hyphenation, normalize whitespace
    3. Detect section headings to attach as metadata
    4. Split using RecursiveCharacterTextSplitter tuned for medical text
    5. Deduplicate near-identical chunks
    6. Embed with bge-small (no prefix — documents side)
    7. Upsert to Qdrant with rich metadata

    Usage:
        python -m app.rag.ingest <pdf_file_or_directory>
    """
    import re
    import sys
    import uuid
    import hashlib
    from pathlib import Path

    from pypdf import PdfReader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from app.core.config import settings
    from app.rag.embedder import embed_batch
    from app.rag.retriever import ensure_collection, upsert_chunks
    from app.rag.local_storage import save_embeddings_locally


    # ── Medical section heading patterns ─────────────────────────────────────────
    SECTION_PATTERNS = re.compile(
        r"^("
        r"abstract|introduction|background|objective[s]?|method[s]?|"
        r"material[s]? and method[s]?|result[s]?|discussion|conclusion[s]?|"
        r"recommendation[s]?|diagnosis|treatment|dosage|contraindication[s]?|"
        r"side effect[s]?|adverse effect[s]?|indication[s]?|warning[s]?|"
        r"pharmacology|clinical trial[s]?|references|appendix|summary|"
        r"epidemiology|pathophysiology|etiology|prognosis|prevention|"
        r"symptoms?|signs?|management|follow[- ]?up|case report"
        r")[\s:.\-]",
        re.IGNORECASE | re.MULTILINE,
    )

    # Patterns that are likely headers/footers/noise to remove
    NOISE_PATTERNS = [
        re.compile(r"^\s*\d+\s*$", re.MULTILINE),           # lone page numbers
        re.compile(r"^.{0,60}(journal|vol\.|doi:|issn).{0,60}$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*(all rights reserved|copyright|©).+$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*page \d+ of \d+\s*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*running head:.+$", re.IGNORECASE | re.MULTILINE),
    ]


    # ── Text cleaning ─────────────────────────────────────────────────────────────

    def _clean_text(text: str) -> str:
        """Clean extracted PDF text for better chunking quality."""

        # Fix hyphenated line breaks (common in PDFs): "treat-\nment" → "treatment"
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

        # Normalize line breaks: single newlines within paragraphs → space
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

        # Remove noise patterns
        for pattern in NOISE_PATTERNS:
            text = pattern.sub("", text)

        # Collapse multiple spaces
        text = re.sub(r" {2,}", " ", text)

        # Collapse 3+ newlines into 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove non-printable characters
        text = re.sub(r"[^\x20-\x7E\n]", " ", text)

        return text.strip()


    def _detect_section(text: str) -> str:
        """Try to detect which medical section this chunk belongs to."""
        match = SECTION_PATTERNS.search(text)
        if match:
            return match.group(0).strip().rstrip(":.-").title()
        return ""


    def _content_hash(text: str) -> str:
        """SHA256 hash of text for deduplication."""
        return hashlib.sha256(text.lower().strip().encode()).hexdigest()


    # ── Page extraction ───────────────────────────────────────────────────────────

    def _extract_pages(pdf_path: Path) -> list[dict]:
        """Extract and clean text from each page."""
        reader = PdfReader(str(pdf_path))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            raw = page.extract_text() or ""
            cleaned = _clean_text(raw)
            if cleaned and len(cleaned) > 30:
                pages.append({"page": i, "text": cleaned})
        return pages


    # ── Chunking ──────────────────────────────────────────────────────────────────

    def _chunk_pages(pages: list[dict], filename: str) -> list[dict]:
        """
        Chunk strategy for medical PDFs:
        - Primary separators: double newline (paragraphs), then sentences
        - Chunk size 400 tokens ~= 300 words — good for medical detail
        - 80 token overlap ensures context continuity across chunks
        - Deduplication via content hash
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=[
                "\n\n",      # paragraph break (most important)
                "\n",        # line break
                ". ",        # sentence end
                "! ",
                "? ",
                "; ",        # clause separator common in medical text
                ", ",
                " ",
                "",
            ],
            length_function=len,
        )

        seen_hashes: set[str] = set()
        chunks = []
        chunk_index = 0

        for page in pages:
            splits = splitter.split_text(page["text"])
            for split in splits:
                text = split.strip()

                # Skip very short fragments
                if len(text) < settings.MIN_CHUNK_LENGTH:
                    continue

                # Deduplicate
                h = _content_hash(text)
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)

                section = _detect_section(text)

                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "filename": filename,
                    "page": page["page"],
                    "section": section,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

        return chunks


    # ── Ingest one PDF ────────────────────────────────────────────────────────────

    def ingest_pdf(pdf_path: Path) -> int:
        """
        Full pipeline for one PDF.
        Returns number of chunks inserted.
        """
        print(f"  📄 Extracting: {pdf_path.name}")
        pages = _extract_pages(pdf_path)
        if not pages:
            print(f"  ⚠  No extractable text in {pdf_path.name} — skipping.")
            return 0

        print(f"  ✂  Chunking {len(pages)} pages...")
        chunks = _chunk_pages(pages, filename=pdf_path.name)
        if not chunks:
            print(f"  ⚠  No valid chunks produced — skipping.")
            return 0

        print(f"  🔢 Embedding {len(chunks)} chunks...")
        texts = [c["text"] for c in chunks]
        vectors = embed_batch(texts)

        # NEW: Save locally first
        print(f"  💾 Saving embeddings locally...")
        save_embeddings_locally(chunks, vectors, pdf_path.name)

        points = [
            {
                "id": c["id"],
                "vector": v,
                "text": c["text"],
                "filename": c["filename"],
                "page": c["page"],
                "section": c["section"],
                "chunk_index": c["chunk_index"],
            }
            for c, v in zip(chunks, vectors)
        ]

        # Ask if user wants to upload to Qdrant now
        upload_now = input(f"  ☁  Upload {len(points)} chunks to Qdrant? (y/n): ").lower()
        if upload_now == 'y':
            print(f"  ☁  Upserting to Qdrant ({settings.QDRANT_COLLECTION})...")
            ensure_collection()
            upsert_chunks(points)
        else:
            print(f"  ⏸ Skipped Qdrant upload. You can upload later using: python -m app.rag.upload_to_qdrant")
        
        print(f"  ✅ {len(points)} chunks from {pdf_path.name}\n")
        return len(points)

    # ── CLI entry ─────────────────────────────────────────────────────────────────

    def main():
        if len(sys.argv) < 2:
            print("Usage: python -m app.rag.ingest <pdf_file_or_directory>")
            sys.exit(1)

        target = Path(sys.argv[1])
        if not target.exists():
            print(f"Error: path not found: {target}")
            sys.exit(1)

        if target.is_dir():
            pdf_files = sorted(target.glob("**/*.pdf"))
            print(f"Found {len(pdf_files)} PDF(s) in {target}\n")
        elif target.suffix.lower() == ".pdf":
            pdf_files = [target]
        else:
            print("Error: must be a .pdf file or directory")
            sys.exit(1)

        if not pdf_files:
            print("No PDFs found.")
            sys.exit(0)

        total = 0
        for pdf in pdf_files:
            print(f"Processing: {pdf.name}")
            total += ingest_pdf(pdf)

        print(f"{'='*50}")
        print(f"✅ Done. Total chunks ingested: {total}")
        print(f"{'='*50}")


    if __name__ == "__main__":
        main()
