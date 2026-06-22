# MedRAG Backend

AI-powered medical knowledge assistant backend with Retrieval-Augmented Generation (RAG) for clinical document Q&A.

## Overview

MedRAG Backend is a FastAPI application that powers a medical chatbot. It ingests PDF documents, embeds them into a vector database, and answers medical questions using Retrieval-Augmented Generation (RAG) with source citations.

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI 0.111.0 |
| **Database** | PostgreSQL 16 (async SQLAlchemy) |
| **Vector DB** | Qdrant Cloud |
| **LLM** | DeepSeek V4 Flash (via deepseek) |
| **Embeddings** | BAAI/bge-small-en-v1.5 (384 dim) |
| **Auth** | JWT (httpOnly cookies) |
| **Migration** | Alembic |
| **Container** | Docker |

## Features

- 🔐 **Authentication** — JWT-based auth with httpOnly cookies, refresh tokens
- 💬 **Chat** — Streaming responses via Server-Sent Events (SSE)
- 📚 **Document Management** — Upload PDFs, list, and delete from knowledge base
- 🔍 **RAG Pipeline** — Semantic search with BGE embeddings, medical-optimized chunking
- 📖 **Conversation History** — Persistent chat history per user
- 🛡️ **Admin Panel** — Admin-only document management endpoints
- ⚡ **Async** — Fully async FastAPI with async SQLAlchemy

## API Endpoints

### Auth
```
POST   /api/auth/register    - Create account
POST   /api/auth/login       - Sign in (sets httpOnly cookies)
POST   /api/auth/refresh     - Refresh JWT token
POST   /api/auth/logout      - Sign out
GET    /api/auth/me          - Get current user
PUT    /api/auth/profile     - Update full name
PUT    /api/auth/password    - Change password
```

### Chat
```
POST   /api/chat             - Non-streaming chat response
POST   /api/chat/stream      - Streaming SSE response
```

### Conversations
```
GET    /api/conversations              - List user conversations
POST   /api/conversations              - Create new conversation
GET    /api/conversations/{id}/messages - Get conversation messages
POST   /api/conversations/{id}/messages - Save a message
DELETE /api/conversations/{id}         - Delete conversation
```

### Admin
```
POST   /api/admin/upload          - Upload PDF (admin only)
GET    /api/admin/documents       - List ingested documents
DELETE /api/admin/documents/{filename} - Delete document
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── admin.py          # Document upload, list, delete
│   │   ├── auth.py           # Register, login, refresh, logout
│   │   ├── chat.py           # Chat endpoints (streaming + non-streaming)
│   │   ├── conversations.py  # Conversation CRUD
│   │   └── schemas.py        # Pydantic schemas
│   ├── core/
│   │   ├── config.py         # Pydantic settings
│   │   ├── deps.py           # Auth dependencies
│   │   └── security.py       # Password hashing, JWT
│   ├── db/
│   │   ├── database.py       # Async SQLAlchemy setup
│   │   └── models.py         # User, Conversation, Message
│   ├── rag/
│   │   ├── embedder.py       # BGE embeddings
│   │   ├── retriever.py      # Qdrant client
│   │   ├── ingest.py         # PDF ingestion pipeline
│   │   ├── prompt.py         # System prompt builder
│   │   └── llm.py            # DeepSeek client
│   └── main.py               # FastAPI app
├── alembic/                   # Database migrations
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## RAG Pipeline

### Ingestion Flow
1. **PDF Extraction** — Extract text per page with `pypdf`
2. **Text Cleaning** — Fix hyphenation, remove noise (page numbers, headers, footers)
3. **Section Detection** — Identify medical sections (Diagnosis, Treatment, Dosage, etc.)
4. **Chunking** — RecursiveCharacterTextSplitter (chunk_size=400, overlap=80)
5. **Deduplication** — SHA256 hash to prevent duplicate chunks
6. **Embedding** — `BAAI/bge-small-en-v1.5` (384 dim)
7. **Upsert** — Push to Qdrant Cloud with metadata (filename, page, section)

### Retrieval Flow
1. **Query Embedding** — BGE query prefix for semantic search
2. **Vector Search** — Qdrant cosine similarity (top_k=6, threshold=0.45)
3. **Context Building** — Sort by score, include source citations
4. **LLM Generation** — DeepSeek V4 Flash via OpenRouter with streaming

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM (OpenRouter)
DEEPSEEK_API_KEY=sk-or-v1-your-key
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_MODEL=deepseek/deepseek-v4-flash

# Qdrant
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION=medical_docs

# Embedding
EMBED_MODEL=BAAI/bge-small-en-v1.5
EMBED_DIMENSION=384

# RAG
TOP_K_RESULTS=6
SCORE_THRESHOLD=0.45
CHUNK_SIZE=400
CHUNK_OVERLAP=80
```

## Local Development

### Prerequisites
- Python 3.11+
- Docker (Postgres + Qdrant)
- Deepseek API key

### Setup

```bash
# Clone and enter directory
git clone https://github.com/yourusername/medical-rag-backend.git
cd medical-rag-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Postgres and Qdrant
docker run -d --name postgres -e POSTGRES_USER=meduser -e POSTGRES_PASSWORD=medpass -e POSTGRES_DB=meddb -p 5432:5432 postgres:16-alpine
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# Create .env
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Ingest a PDF

```bash
docker exec -it backend-1 python -m app.rag.ingest docs/your-file.pdf
```

## Deployment

### Docker

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### AWS EC2

1. Launch Ubuntu 24.04 LTS (t2.micro)
2. Install Docker and Docker Compose
3. Upload code via SCP
4. Create `.env` with cloud credentials
5. Build and run: `docker compose -f docker-compose.prod.yml up -d --build`
6. Run migrations: `docker exec backend-1 alembic upgrade head`

## License

Private — for authorized use only.