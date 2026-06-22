from openai import AsyncOpenAI
from app.core.config import settings

_client: AsyncOpenAI | None = None


def get_deepseek_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Medical RAG Advisor",
            },
        )
    return _client


async def generate_answer(messages: list[dict]) -> str:
    """
    Send messages to DeepSeek and return the full response text.
    Uses non-streaming for simplicity; see generate_answer_stream for SSE.
    """
    client = get_deepseek_client()
    response = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=messages,
        max_tokens=settings.DEEPSEEK_MAX_TOKENS,
        temperature=settings.DEEPSEEK_TEMPERATURE,
        stream=False,
    )
    return response.choices[0].message.content or ""


async def generate_answer_stream(messages: list[dict]):
    """
    Async generator that yields text chunks for Server-Sent Events.
    Usage: async for chunk in generate_answer_stream(messages): ...
    """
    client = get_deepseek_client()
    stream = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=messages,
        max_tokens=settings.DEEPSEEK_MAX_TOKENS,
        temperature=settings.DEEPSEEK_TEMPERATURE,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
