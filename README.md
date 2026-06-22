# MedRAG — Medical Knowledge Assistant

Full-stack AI-powered medical chatbot with Retrieval-Augmented Generation (RAG) for clinical document Q&A.

## Overview

MedRAG is a complete medical knowledge assistant that allows healthcare professionals to query their clinical document library using natural language. It combines:

- **RAG Pipeline** — Semantic search over ingested PDFs with source citations
- **Real-time Streaming** — Server-Sent Events for ChatGPT-like responses
- **Conversation History** — Persistent chat history per user
- **Admin Panel** — Document management interface

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                     │
│                         Vercel (HTTPS)                        │
├─────────────────────────────────────────────────────────────────┤
│                      Next.js API Proxy                        │
│                   (Routes to Backend)                         │
├─────────────────────────────────────────────────────────────────┤
│                         Backend (FastAPI)                     │
│                         AWS EC2 (HTTP/HTTPS)                  │
├───────────────┬──────────────────┬────────────────────────────┤
│   PostgreSQL  │    Qdrant Cloud  │    Deepseek API          │
│   (Neon)      │   (Vector DB)    │   (DeepSeek LLM)           │
├───────────────┴──────────────────┴────────────────────────────┤
│                         PDF Documents                         │
│                      (Ingested via Admin)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 🔐 Authentication
- JWT-based auth with httpOnly cookies
- Register, login, logout, refresh
- Role-based access (admin vs regular users)
- Protected routes with Next.js middleware

### 💬 Chat
- Real-time streaming responses (SSE)
- Source citations with filename, page, excerpt
- Medical disclaimer on every answer
- Copy to clipboard
- Auto-scroll to latest message
- Suggestions for common medical questions

### 📚 Document Management (Admin)
- Drag-and-drop PDF upload
- Upload progress indicator
- List all ingested documents with chunk counts
- Delete documents from knowledge base

### 📖 Conversation History
- Persistent chat history per user
- Auto-generated titles from first message
- Click to continue previous conversations
- Delete conversations

### 👤 User Profile
- View and update full name
- Change password (requires current password)
- Email is read-only

### 🎨 UI/UX
- Dark/light mode toggle
- Responsive sidebar navigation
- Loading skeletons
- Toast notifications
- Mobile-friendly

## Tech Stack

### Frontend

| Component | Technology |
|-----------|------------|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS 4 |
| Components | shadcn/ui (Base UI) |
| Icons | Lucide React |
| Dark Mode | next-themes |
| Forms | react-hook-form + Zod |
| Toasts | Sonner |

### Backend

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.111.0 |
| Language | Python 3.11 |
| Database | PostgreSQL 16 (async SQLAlchemy) |
| Vector DB | Qdrant Cloud |
| LLM | DeepSeek V4 Flash  |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Auth | JWT (httpOnly cookies) |
| Migrations | Alembic |

### Infrastructure

| Component | Provider |
|-----------|----------|
| Frontend | Vercel (Hobby) |
| Backend | AWS EC2 t2.micro |
| Database | Neon (Free Tier) |
| Vector DB | Qdrant Cloud (Free Tier) |
| SSL | Let's Encrypt + Nginx |

## Project Structure

```
medical-rag/
├── frontend/
│   ├── app/
│   │   ├── (auth)/           # Login & Register
│   │   ├── (protected)/      # Chat, Profile, Admin
│   │   ├── api/[...path]/    # API proxy to backend
│   │   └── middleware.ts     # Route protection
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── chat-window.tsx
│   │   ├── sidebar.tsx
│   │   ├── admin-view.tsx
│   │   └── ...
│   └── lib/
│       ├── api.ts            # API client with token refresh
│       ├── auth.ts           # Auth functions
│       └── types.ts          # TypeScript interfaces
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers
│   │   ├── core/             # Config, auth, security
│   │   ├── db/               # Database models
│   │   └── rag/              # RAG pipeline
│   ├── alembic/              # Migrations
│   └── requirements.txt
└── docker-compose.yml
```

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker
- Deepseek API key
- Qdrant Cloud account (or local Qdrant)

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
docker run -d --name postgres -e POSTGRES_USER=meduser -e POSTGRES_PASSWORD=medpass -e POSTGRES_DB=meddb -p 5432:5432 postgres:16-alpine
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Docker Setup

```bash
docker compose up -d --build
docker exec backend-1 alembic upgrade head
docker exec backend-1 python -m app.rag.ingest docs/your-file.pdf
```

## Deployment

### Frontend (Vercel)

```bash
cd frontend
npm run build
vercel --prod
```

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL` — Your backend URL (HTTPS recommended)
- `NEXT_PUBLIC_APP_NAME` — Medical RAG Advisor

### Backend (AWS EC2)

1. Launch Ubuntu 24.04 LTS (t2.micro)
2. Install Docker: `curl -fsSL https://get.docker.com | sh`
3. Upload code via SCP
4. Create `.env` with cloud credentials (Neon, Qdrant Cloud, Deepseek api)
5. Build and run: `docker compose -f docker-compose.prod.yml up -d --build`
6. Run migrations: `docker exec backend-1 alembic upgrade head`
7. (Optional) Set up Nginx reverse proxy + Let's Encrypt SSL

### Database (Neon)
- Sign up at neon.tech
- Create project, copy connection string
- Use connection string in `DATABASE_URL`

### Vector DB (Qdrant Cloud)
- Sign up at cloud.qdrant.io
- Create cluster (Free Tier)
- Copy URL and API key
- Create collection: `medical_docs` (dimension: 384)

## API Endpoints

### Auth
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me
PUT    /api/auth/profile
PUT    /api/auth/password
```

### Chat
```
POST   /api/chat
POST   /api/chat/stream
```

### Conversations
```
GET    /api/conversations
POST   /api/conversations
GET    /api/conversations/{id}/messages
POST   /api/conversations/{id}/messages
DELETE /api/conversations/{id}
```

### Admin
```
POST   /api/admin/upload
GET    /api/admin/documents
DELETE /api/admin/documents/{filename}
```

## Environment Variables

### Frontend `.env.local`
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_NAME=Medical RAG Advisor
```

### Backend `.env`
```env
# Database
DATABASE_URL=postgresql://user:pass@neon.tech/neondb

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
DEEPSEEK_API_KEY=sk-or-v1-your-key
DEEPSEEK_BASE_URL = 
DEEPSEEK_MODEL=deepseek-v4-flash

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Private — for authorized use only.

## Contact

For questions or support, please open an issue on GitHub.