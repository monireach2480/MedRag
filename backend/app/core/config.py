from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Medical RAG API"
    DEBUG: bool = False

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Qdrant — use QDRANT_URL for cloud, host/port for local
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = ""  # Set in .env
    QDRANT_API_KEY: str = ""  # Set in .env
    QDRANT_COLLECTION: str = "medical_docs"

    # DeepSeek via OpenRouter
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_MAX_TOKENS: int = 1024
    DEEPSEEK_TEMPERATURE: float = 0.3

    # Embedding — bge-small fits t2.micro, still great quality
    EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBED_DIMENSION: int = 384

    # Chunking — tuned for medical PDFs
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 80
    MIN_CHUNK_LENGTH: int = 50

    # RAG retrieval
    TOP_K_RESULTS: int = 6
    SCORE_THRESHOLD: float = 0.45  # ignore chunks below this similarity

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()