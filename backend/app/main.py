from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import create_tables
from app.rag.retriever import ensure_collection
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    ensure_collection()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,          prefix="/api")
app.include_router(chat_router,          prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(admin_router,         prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
