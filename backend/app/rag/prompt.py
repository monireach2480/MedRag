from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are a precise and careful medical information assistant.
Your answers are grounded ONLY in the provided medical documents.

Core rules:
- Answer ONLY from the provided context. Never fabricate information.
- Never invent drug names, dosages, diagnoses, or treatment protocols.
- If the context is insufficient, clearly say: "The documents I have access to don't contain enough information to answer this accurately."
- Always recommend consulting a qualified healthcare professional for personal medical decisions.
- Be concise, accurate, and use plain language. Avoid unnecessary jargon.
- For drug dosages or clinical protocols, quote the source document section directly.
- If multiple documents give conflicting information, mention the conflict explicitly.
- Do not answer questions unrelated to medicine or healthcare.

Response format:
- Use short paragraphs for readability.
- If listing symptoms, drugs, or steps — use a simple list.
- End with the source document reference naturally in your answer."""


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> list[dict]:
    """
    Build an OpenAI-compatible messages list for DeepSeek.
    Chunks are ordered by score (best first) and include section metadata.
    """
    if not chunks:
        context_block = (
            "No relevant documents were found in the knowledge base for this query. "
            "Please inform the user that you cannot find relevant information."
        )
    else:
        # Sort by score descending — best chunks first
        sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)

        sections = []
        for i, chunk in enumerate(sorted_chunks, 1):
            section_label = f" — {chunk.section}" if chunk.section else ""
            header = f"[Source {i}: {chunk.filename}, page {chunk.page}{section_label}]"
            sections.append(f"{header}\n{chunk.text}")

        context_block = "\n\n---\n\n".join(sections)

    user_content = (
        f"Medical documents context:\n\n"
        f"{context_block}\n\n"
        f"{'='*60}\n\n"
        f"Question: {query}\n\n"
        f"Answer based only on the documents above. "
        f"Reference the source document naturally in your response."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]
