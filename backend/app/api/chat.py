import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, AsyncSessionLocal
from app.db.models import User, Conversation, Message
from app.core.deps import get_current_user
from app.rag.retriever import search
from app.rag.prompt import build_prompt
from app.rag.llm import generate_answer, generate_answer_stream
from app.api.schemas import ChatRequest, ChatResponse, SourceDocument

router = APIRouter(prefix="/chat", tags=["chat"])

DISCLAIMER = (
    "This response is for informational purposes only and does not constitute "
    "medical advice. Always consult a qualified healthcare professional."
)


async def _get_or_create_conversation(
    db: AsyncSession, user: User, conversation_id: int | None, first_message: str
) -> Conversation:
    from sqlalchemy import select
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return conv

    title = first_message[:60].strip()
    if len(first_message) > 60:
        title += "..."

    conv = Conversation(user_id=user.id, title=title)
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


# ── Non-streaming ─────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await _get_or_create_conversation(db, current_user, body.conversation_id, body.message)

    try:
        chunks = search(body.message)
        messages_prompt = build_prompt(body.message, chunks)
        answer = await generate_answer(messages_prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM or retrieval error: {str(exc)}",
        )

    sources = [
        SourceDocument(
            filename=c.filename,
            page=c.page,
            excerpt=c.text[:200] + ("…" if len(c.text) > 200 else ""),
        )
        for c in chunks
    ]
    sources_dict = [s.model_dump() for s in sources]

    db.add(Message(conversation_id=conv.id, role="user", content=body.message))
    db.add(Message(conversation_id=conv.id, role="assistant", content=answer, sources=sources_dict))
    await db.flush()

    return ChatResponse(answer=answer, sources=sources, disclaimer=DISCLAIMER)


# ── Streaming (SSE) ───────────────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Server-Sent Events stream.
    Events:
        {"type":"conversation_id", "conversation_id": 1}
        {"type":"chunk",    "content":"..."}
        {"type":"sources",  "sources":[...], "disclaimer":"..."}
        {"type":"done"}
        {"type":"error",    "detail":"..."}
    """
    conv = await _get_or_create_conversation(db, current_user, body.conversation_id, body.message)
    conv_id = conv.id
    user_id = current_user.id

    # Persist user message before streaming starts
    db.add(Message(conversation_id=conv_id, role="user", content=body.message))
    await db.flush()
    await db.commit()

    chunks = search(body.message)
    messages_prompt = build_prompt(body.message, chunks)

    sources_payload = [
        {
            "filename": c.filename,
            "page": c.page,
            "excerpt": c.text[:200] + ("…" if len(c.text) > 200 else ""),
        }
        for c in chunks
    ]

    async def event_generator():
        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conv_id})}\n\n"

        full_answer = ""
        try:
            async for token in generate_answer_stream(messages_prompt):
                full_answer += token
                yield f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n"

            # Persist assistant message using a fresh session
            async with AsyncSessionLocal() as save_db:
                save_db.add(Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_answer,
                    sources=sources_payload,
                ))
                await save_db.commit()

            yield f"data: {json.dumps({'type': 'sources', 'sources': sources_payload, 'disclaimer': DISCLAIMER})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
