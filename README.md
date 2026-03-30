# WorkPulse

Your AI-powered work assistant for intelligent email, chat, and task management.

A comprehensive AI Work Intelligence Assistant that transforms emails, chats, and tasks into actionable insights using retrieval-augmented generation (RAG), embeddings, and agentic AI.

**Key Capabilities:**
- 📧 **Email & Chat Sync**: Fetch from Microsoft Outlook & Teams via Graph API
- 🧠 **RAG-Powered Chat**: Ask questions about your work data with source citations
- ⚡ **AI Actions**: Summarize emails, extract tasks, generate daily reports
- 🔍 **Vector Search**: FAISS-based semantic search with embeddings
- 🔐 **Secure & Isolated**: Per-user data isolation, OAuth2 authentication
- 🤖 **LLM Agnostic**: Groq/Qwen primary, fallback to OpenAI/Gemini for embeddings

## Architecture

```
Frontend (React + Vite) ──┐
                          │
                    localhost:8080
                          │
                          ▼
Backend (FastAPI + Python 3.13)
    ├─ Auth Layer (Microsoft OAuth)
    ├─ Data Pipeline (fetch → process → embed → index)
    ├─ RAG Engine (query embedding + FAISS + Mongo + LLM)
    ├─ Action Engine (intent detection + task extraction)
    └─ Chat Endpoints (data-grounded + unread counts)
        │
        ├─ MongoDB (messages, users, history)
        ├─ FAISS (in-memory vector store)
        ├─ Microsoft Graph (Outlook, Teams API)
        ├─ Groq (Qwen model for generation)
        └─ OpenAI/Gemini (embeddings fallback)
```

## Features

### 1. Authentication & Authorization
- **OAuth 2.0** with Microsoft Identity Platform (Azure AD)  
- `POST /auth/login` → Redirect to Microsoft consent screen
- `GET /auth/callback` → Exchange auth code for tokens
- `GET /auth/me` → Get current user profile (token-validated)
- `POST /auth/logout` → Clear session
- Cookie-based session management with `work_intel_access_token`
- Per-user data isolation enforced on all protected endpoints

### 2. Data Pipeline (End-to-End)

**Fetch** — `POST /data/fetch`
- Retrieves raw emails and chats from Microsoft Graph
- Returns: user profile, emails, chats, messages

**Sync & Process** — `POST /data/sync` (Complete Pipeline)
- Fetches data from Microsoft Graph
- Text cleaning and normalization
- Word-boundary chunking (300 chars per chunk)
- Embedding generation (OpenAI → Gemini → local fallback)
- Vector indexing into FAISS
- Stores processed chunks in MongoDB
- Includes deduplication and conflict resolution
- Returns: documents_saved, documents_indexed

**Direct Process** — `POST /data/process` (Alternative)
- Same pipeline as /data/sync (for advanced workflows)
- Useful if you want separate fetch and process steps

### 3. RAG-Powered Chat
- **`POST /chat`** — Query your indexed work data
  - Embeds query using same provider as training data
  - Searches FAISS for top-5 similar chunks
  - Fetches full documents from MongoDB
  - Generates response using Groq/Qwen
  - Returns: answer + source citations
  - **Special**: Detects "unread mail" queries → fetches live count from Graph

### 4. AI Actions (Agentic System)
- **Summarize Emails** — Overview, highlights, risks, next steps
- **Extract Tasks** — JSON array of actionable tasks with deadlines
- **Generate Daily Report** — Executive summary + priorities + blockers
- **Intent Detection** — Routes user queries to appropriate action  
- **Multi-turn Agent** — Handles conversation routing via `/agent`

### 5. LLM Services
- **Primary**: Groq API with Qwen model (`qwen/qwen3-32b`)
- **Methods**:
  - `generate_text()` → Single completion
  - `generate_json()` → Structured output with auto-retry
- Configuration via `GROQ_API_KEY` + `GROQ_MODEL`

### 6. Embedding Strategy (Multi-Tier)
- **Tier 1**: OpenAI `text-embedding-3-small` 
- **Tier 2**: Gemini `text-embedding-004`
- **Tier 3**: Local SHA256-based fallback (256-dim)
- Graceful fallthrough if higher tier fails

### 7. Vector Store
- **FAISS** in-memory index with doc_id mapping
- Fallback to cosine similarity if FAISS unavailable
- Lazy re-indexing on first empty query (auto-hydration)

### 8. Health & Monitoring
- `GET /health` → Service status
- `GET /health/db` → Database connectivity
- `GET /actions/models` → Active LLM provider info

---

## Setup & Installation

### Prerequisites
- Python 3.13+
- MongoDB Atlas cluster (or local MongoDB)
- Microsoft Azure AD tenant + app registration
- Groq API key (+ optional OpenAI, Gemini for fallbacks)
- Node.js 18+ (for frontend)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: .\venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
```

### Frontend Setup

```bash
cd ..  # Return to root
npm install
npm run dev  # Starts on localhost:8080
```

### Required Environment Variables

```ini
# Microsoft Azure AD
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
REDIRECT_URI=http://localhost:8000/auth/callback

# MongoDB
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
DATABASE_NAME=ai_work_assistant

# LLM - Groq (Primary)
GROQ_API_KEY=your_groq_key
GROQ_MODEL=qwen/qwen3-32b

# Embeddings - OpenAI (Fallback)
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Embeddings - Gemini (Fallback)
GEMINI_API_KEY=...
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

### Azure AD Configuration

In Azure Portal:
1. Register new app
2. Add **Microsoft Graph** delegated permissions:
   - `User.Read` (required)
   - `Mail.Read` (for emails)
   - `Chat.Read` (for Teams chats)
   - `ChatMessage.Read` (for messages)
3. Grant admin consent
4. Create client secret
5. Add Redirect URI: `http://localhost:8000/auth/callback`

### Run Services

```bash
# Terminal 1 - Backend
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
npm run dev
```

Visit: **http://localhost:8080**

---

## Usage Workflow

### 1. Authenticate
- Go to http://localhost:8080
- Click "Continue with Microsoft"
- Grant consent for Mail.Read, Chat.Read scopes

### 2. Sync Your Data
Go to **Data Sources** tab:
- Click **"1. Fetch Data"** → Get raw emails/chats from Graph
- Click **"2. Process & Index"** → Chunk, embed, and index into Mongo + FAISS
- Click **"Sync"** → Incremental updates (optional)

### 3. Ask Chat Questions
Go to **AI Chat** tab and ask:
- "How many unread mails do I have?"
- "Summarize this week's key discussions"
- "What tasks are pending?"
- Responses include source citations

### 4. Run AI Actions
Go to **Actions** tab and click:
- **Summarize Emails** → Overview + highlights + risks + next steps
- **Extract Tasks** → Numbered tasks with deadlines
- **Generate Report** → Executive summary + priorities + blockers

### 5. View Dashboard
- Email & chat counts
- Quick action cards
- Recent activity
- Data sync status

## Quickstart

### Prerequisites

- Python 3.13+ (`python --version`)
- Node.js + npm (for frontend)
- MongoDB Atlas cluster
- Azure AD app registration with Graph permissions

### Install dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Configure environment

Create `.env` from `.env.example` and update values:

```ini
CLIENT_ID=<azure-client-id>
CLIENT_SECRET=<azure-client-secret>
TENANT_ID=<azure-tenant-id>
REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:8080
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/work_intelligence?retryWrites=true&w=majority
DATABASE_NAME=work_intelligence
```

### Azure AD app registration setup (graph scopes)

- `API permissions` > `Microsoft Graph` > `Delegated permissions`:
  - `User.Read`
  - `Mail.Read` (for emails)
  - `Chat.Read` (Teams chats)
  - `ChatMessage.Read` (chat messages)
- **Grant admin consent** for the tenant *if required*

### Run backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run frontend

```bash
cd ..   # root from backend -> main workspace
npm run dev
```

## API Documentation

### Authentication

- `GET /auth/login` -> Azure login redirect
- `GET /auth/callback` -> handles auth code; sets token cookie; redirects frontend
- `GET /auth/me` -> returns user profile or 401
- `POST /auth/logout` -> clears cookie

### Data

- `GET /data/fetch` (header or query token) -> returns user, emails, chats, messages

### Health

- `GET /health` -> basic server health
- `GET /health/db` -> DB health

## Troubleshooting

### `Need admin approval` from Azure

- Ensure app has proper permissions and admin consent on Azure AD.
- If necessary, start with only `User.Read` and later add `Mail.Read`, `Chat.Read`, `ChatMessage.Read`.

### `MongoDB connection failed`

- Make sure `MONGODB_URI` is correct (with `/work_intelligence?retryWrites=true&w=majority`)
- Check network access whitelists in Atlas (`0.0.0.0/0` for dev) and credentials.

### `/auth/login 307` with `action=authorize`

- Expected behavior: redirect to Microsoft login.
- If it doesn’t continue to callback, verify Azure app `Redirect URI` and permission consent.

## API Reference

### Authentication
- `POST /auth/login` — Redirect to Microsoft OAuth
- `GET /auth/callback?code=...` — OAuth callback (internal handling)
- `GET /auth/me` — Get current user profile  
- `POST /auth/logout` — Clear session cookie

### Data Pipeline
- `POST /data/fetch` — Get raw emails/chats from Microsoft Graph
- `POST /data/sync` — Sync & deduplicate to MongoDB
- `POST /data/process` — Process, chunk, embed, and index

### Chat & RAG
- `POST /chat` — Query indexed data with RAG + citations

### Actions
- `POST /actions/run` — Execute action
- `GET /actions/models` — Get active LLM provider
- `POST /agent` — Multi-turn intent routing

### Health
- `GET /health` → Service status
- `GET /health/db` → Database connectivity

---

## Database Schema

### `messages` Collection
- `user_id`, `source` (outlook|teams), `message_id`, `content`
- `metadata`: participants, subject, team info, chunk indices
- **Unique Index**: `(user_id, source, message_id, metadata.chunk_index)` (sparse)

### `users` Collection
- `userPrincipalName`, `mail`, `displayName`, `token`, `created_at`

---

## Troubleshooting

**Chat not using my data?**
- Verify `/data/fetch` returns emails/messages
- Verify `/data/process` shows `documents_saved > 0`
- Confirm `/auth/me` returns valid user

**Embeddings failing?**
- Tier 1 (OpenAI) → Tier 2 (Gemini) → Tier 3 (local)
- Check logs for which tier was used

**MongoDB E11000 errors?**
```bash
db.messages.deleteMany({source: null})
db.messages.dropIndex("uniq_user_source_message")
# Then re-run /data/process
```

---

## Project Structure

```
workpulse/
├── backend/
│   ├── routes/ (auth, chat, actions, data)
│   ├── services/ (llm, rag, embedding, processor, vector_store, graph_api)
│   ├── db/ (mongodb)
│   └── main.py
├── src/
│   ├── pages/ (Login, Dashboard, AIChat, Actions, DataSources)
│   └── components/
└── README.md
```

---

## Roadmap

- [ ] Persistent vector DB (Pinecone/Weaviate)
- [ ] Multi-turn conversation memory
- [ ] Google Workspace integration
- [ ] Calendar analytics

---

## License

Proprietary — Artesian Technologies 2026

---

**Last Updated**: March 30, 2026  
**Version**: 1.0.0  
**Status**: Production-Ready
