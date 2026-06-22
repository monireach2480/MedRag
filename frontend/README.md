# MedRAG — Medical Knowledge Assistant Frontend

A Next.js frontend for a retrieval-augmented medical chatbot that answers questions from clinical documents with cited sources.

## Overview

MedRAG is a clinical knowledge assistant that allows healthcare professionals to query their document library using natural language. The frontend provides:

- 🔐 **Authentication** — Sign up, login, and session management with JWT cookies
- 💬 **Conversational AI** — Chat with an LLM grounded in your ingested documents
- 📚 **Document Management** — Upload PDFs (admin only) and see what's in the knowledge base
- 🔍 **Source Citations** — Every answer includes references to specific documents and pages
- 🌗 **Dark/Light Mode** — System-aware theming with manual toggle

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **Next.js 16** | React framework with App Router |
| **TypeScript** | Type-safe code |
| **Tailwind CSS 4** | Utility-first styling |
| **Base UI** | Headless React components (shadcn/base) |
| **React Hook Form + Zod** | Form validation |
| **Sonner** | Toast notifications |
| **Vercel Analytics** | Production usage tracking |

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/           # Login & Register pages (unauthenticated layout)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (protected)/      # Chat, Profile, Admin (authenticated layout)
│   │   ├── admin/page.tsx
│   │   ├── chat/page.tsx
│   │   └── profile/page.tsx
│   ├── api/[...path]/    # API proxy to backend
│   ├── globals.css       # Global styles & theme variables
│   └── layout.tsx        # Root layout with ThemeProvider
├── components/
│   ├── ui/               # shadcn/ui components (Base UI)
│   ├── admin-view.tsx
│   ├── app-shell.tsx
│   ├── auth-provider.tsx
│   ├── chat-window.tsx
│   ├── conversations-provider.tsx
│   ├── message-bubble.tsx
│   ├── sidebar.tsx
│   ├── source-card.tsx
│   ├── theme-toggle.tsx
│   └── upload-dropzone.tsx
├── lib/
│   ├── api.ts            # API client with token refresh
│   ├── auth.ts           # Auth & chat API functions
│   ├── types.ts          # TypeScript interfaces
│   └── utils.ts          # cn() utility
├── middleware.ts         # Route protection & redirects
├── next.config.mjs
├── package.json
└── tsconfig.json
```

## Environment Variables

Create a `.env.local` file in the project root:

```env
BACKEND_URL=https://medicalrag.duckdns.org
```

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | FastAPI backend URL | `https://medicalrag.duckdns.org` |

> **Note:** The `BACKEND` variable in `app/api/[...path]/route.ts` uses `process.env.BACKEND_URL`. Make sure to set this in your deployment environment.

## Getting Started

### Prerequisites

- Node.js 18+
- npm, pnpm, or yarn

### Installation

```bash
cd frontend
npm install
# or
pnpm install
```

### Development

```bash
npm run dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm run start
```

## Features

### Authentication Flow

- **Middleware** protects `/chat`, `/profile`, `/admin` routes
- Unauthenticated users are redirected to `/login`
- Authenticated users are redirected to `/chat` from auth pages
- JWT stored as httpOnly cookie (set by backend)
- Token refresh on 401 responses

### Chat Interface

- Real-time streaming responses via Server-Sent Events
- Conversation history stored per user
- Source citations displayed with excerpts and page numbers
- Medical disclaimer on every AI response
- Keyboard shortcuts: `Enter` to send, `Shift+Enter` for new line

### Document Upload (Admin)

- Drag-and-drop or click to upload PDFs
- Progress indicator during upload
- View all ingested documents with chunk counts
- Delete documents (removes from vector store)

### User Profile

- Update full name
- Change password (requires current password)
- Email is read-only (immutable)

### Theme Support

- System preference detection
- Manual toggle between light/dark
- Persistent preference via `next-themes`

## API Proxy

The frontend includes an API route (`app/api/[...path]/route.ts`) that proxies requests to the backend. This:

- Forwards cookies for authentication
- Handles CORS by using same-origin requests
- Passes through `Set-Cookie` headers

### Backend Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login` | POST | Sign in |
| `/api/auth/register` | POST | Create account |
| `/api/auth/logout` | POST | Sign out |
| `/api/auth/me` | GET | Get current user |
| `/api/auth/profile` | PUT | Update profile |
| `/api/auth/password` | PUT | Change password |
| `/api/auth/refresh` | POST | Refresh JWT |
| `/api/chat/stream` | POST | Stream AI response |
| `/api/conversations` | GET/POST | List/create conversations |
| `/api/conversations/{id}/messages` | GET/POST | Get/save messages |
| `/api/conversations/{id}` | DELETE | Delete conversation |
| `/api/admin/documents` | GET | List ingested documents |
| `/api/admin/upload` | POST | Upload PDF |
| `/api/admin/documents/{filename}` | DELETE | Delete document |

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

Set the `BACKEND_URL` environment variable in your Vercel project settings.

### Docker

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Deployment

| Platform | Variable |
|----------|----------|
| Vercel | `BACKEND_URL` |
| Docker | `-e BACKEND_URL=https://your-backend.com` |
| CLI | `BACKEND_URL=https://your-backend.com npm run build` |

## Development Notes

### TypeScript

The project uses strict TypeScript with path aliases:

```ts
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
```

### Styling

- Tailwind CSS 4 with OKLCH color tokens
- shadcn/ui component system (Base UI primitives)
- `tw-animate-css` for animation utilities

### Component Patterns

- **Providers**: Auth, Conversations, Theme
- **HOCs**: `useAuth()`, `useConversations()` hooks
- **Forms**: React Hook Form + Zod validation
- **API**: Centralized `apiFetch` with automatic token refresh

## License

Private — for authorized use only.