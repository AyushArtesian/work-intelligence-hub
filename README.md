# Work Intelligence Hub

Your AI-powered workplace assistant for intelligent email, chat, and task management.

A comprehensive AI Work Intelligence Hub that transforms emails, Teams chats, and communications into actionable insights using retrieval-augmented generation (RAG), embeddings, and agentic AI.

**Key Capabilities:**
- 📊 **Dashboard** - Real-time email and chat counts, pending actions, key insights
- 📑 **AI-Generated Insights** - Weekly summaries, key decisions, risks, and trends
- 📧 **Email & Chat Sync** - Fetch from Microsoft Outlook & Teams via Graph API with incremental updates
- 💬 **RAG-Powered Chat** - Ask questions about your work data with source citations
- ⚡ **AI Actions** - Summarize emails, extract tasks, generate daily reports
- 🔍 **Vector Search** - FAISS-based semantic search with embeddings
- 🔐 **Secure & Isolated** - Per-user data isolation, OAuth2 authentication
- 🤖 **LLM Powered** - Groq/Qwen for generation, multi-tier embedding strategy

## Architecture

```
Frontend (React 18 + Vite + TypeScript)  ◄── http://localhost:8080
    ├─ Pages: Login, Dashboard, AIChat, Actions, Insights, DataSources, Settings
    ├─ Components: Sidebar, TopNavbar, UI library (shadcn/ui)
    └─ Features: Real-time sync indicators, error handling, loading states
                          │
                    HTTP/REST API
                          │
Backend (FastAPI + Python 3.13)  ◄── http://localhost:8000
    ├─ Auth Middleware (Microsoft OAuth 2.0)
    ├─ Data Pipeline (fetch → process → chunk → embed → index)
    ├─ RAG Engine (query embedding + FAISS vector search + context retrieval)
    ├─ Insights Engine (LLM analysis of work patterns)
    ├─ Action Engine (intent detection + task extraction + summarization)
    └─ Chat Endpoints (multi-turn conversations with data grounding)
        │
        ├─ Storage:
        │   ├─ MongoDB (messages, users, sync history, embeddings metadata)
        │   └─ FAISS (in-memory vector index with doc_id mapping)
        │
        └─ External APIs:
            ├─ Microsoft Graph (Outlook, Teams Chat, User Profile)
            ├─ Groq API (Qwen model for text generation)
            └─ OpenAI/Gemini (embeddings with fallback strategy)
```

## Features

### 1. Dashboard
- **Real-time Stats**: Email count, Teams chats count, chat messages count, data sources count
- **Key Insights**: Summary of emails in inbox, Teams connections, message activity, Microsoft Graph API sync status
- **Pending Actions**: Quick links to view emails, review Teams conversations, check message activity, configure data sources
- **Quick Actions**: Summarize emails, show pending tasks, generate daily report

### 2. AI-Generated Insights
- **Weekly Summary**: Activity patterns, email/chat volume analysis, response time trends, meeting reschedules
- **Key Decisions**: Important decisions identified from communications
- **Risks Identified**: Potential risks, deadline slips, team concerns flagged in conversations
- **Trends**: Cross-team collaboration metrics, communication channel preferences, task completion rates
- Uses LLM to analyze past 7 days of indexed messages and generate structured insights
- Auto-refresh on mount; shows loading state while generating

### 3. Authentication & Authorization
- **OAuth 2.0** with Microsoft Identity Platform (Azure AD)  
- `POST /auth/login` → Redirect to Microsoft consent screen
- `GET /auth/callback` → Exchange auth code for tokens, set secure cookie
- `GET /auth/me` → Get current user profile (token-validated)
- `POST /auth/logout` → Clear session and redirect
- Cookie-based session management with `work_intel_access_token`
- Per-user data isolation enforced on all protected endpoints
- Automatic token refresh on expiry

### 4. Data Pipeline (Complete Workflow)

**Fetch** — `POST /data/fetch`
- Retrieves raw emails (up to 100 most recent) and chats (up to 50) from Microsoft Graph
- Fetches messages from all available chats (up to 50 per chat)
- No data persistence; returns live API data
- Response: user profile, emails, chats, messages grouped by chat_id

**Sync & Process** — `POST /data/sync` (Recommended)
- Full incremental sync based on `last_sync_timestamp`
- Fetches new emails/chats since last sync
- Text cleaning (HTML tags removed, whitespace normalized)
- Word-boundary chunking (300 chars per chunk)
- Embedding generation with fallback strategy
- Vector indexing into FAISS
- Deduplication: `user_id + source + message_id + chunk_index`
- Stores processed documents in MongoDB `messages` collection
- Updates `users.last_sync_timestamp`
- Returns: `documents_saved`, `documents_indexed`, `is_incremental` flag

**Direct Process** — `POST /data/process` (Alternative)
- Same as `/data/sync` but without incremental filtering
- Fetches all available data regardless of last sync time
- Useful for manual full re-indexing

### 5. Insights Generation
- **`POST /data/insights`** — AI-powered analysis of recent communications
  - Queries MongoDB for messages from past 7 days
  - Passes content to LLM with structured prompt
  - Generates: weekly_summary, key_decisions, risks, trends
  - Returns JSON with 2-4 items per category
  - Handles cold starts gracefully if no data exists

### 6. RAG-Powered Chat
- **`POST /chat/send`** — Query indexed work data with context
  - Embeds user query using same provider as training data
  - Searches FAISS for top-5 semantically similar chunks
  - Retrieves full document context from MongoDB
  - Generates response using Groq API (Qwen model)
  - Returns: assistant message + source citations + conversation history
  - Supports multi-turn conversations with context preservation
  - **Special Feature**: Detects "unread mail" queries → fetches live count from Graph API

### 7. AI Actions (Agentic System)
- **Summarize Emails** — Generates overview, highlights, risks, next steps
- **Extract Tasks** — Identifies actionable items with deadlines as JSON array
- **Generate Daily Report** — Executive summary, priorities, blockers, next steps
- **Intent Detection** — Routes queries to appropriate action
- **Multi-turn Agent** — Conversational routing via `/agent` endpoint
- Powered by Groq LLM with structured JSON outputs

### 8. LLM Services
- **Primary**: Groq API with Qwen model (`qwen/qwen3-32b`)
- **Methods**:
  - `generate_text(system_prompt, user_prompt)` → Single text completion
  - `generate_json(system_prompt, user_prompt, default)` → Structured JSON with retry logic
- Automatic JSON extraction with markdown fence detection
- Retry once if first JSON parse fails
- Configuration via environment: `GROQ_API_KEY`, `GROQ_MODEL`

### 9. Embedding Strategy (Multi-Tier Fallback)
- **Tier 1**: OpenAI `text-embedding-3-small` 
- **Tier 2**: Gemini `text-embedding-004`
- **Tier 3**: Local SHA256-based hash (256-dim vector)
- Graceful fallthrough if higher tier fails or API unavailable
- Consistent dimensionality across all tiers for FAISS compatibility

### 10. Vector Store & Search
- **FAISS** in-memory index optimized for fast similarity search
- Doc ID mapping for retrieval from MongoDB
- Cosine similarity fallback if FAISS unavailable
- Lazy re-indexing on first empty query (auto-hydration from MongoDB)
- Top-5 results returned for user queries

### 11. Data Sources Management
- View connected data sources (emails, chats)
- Trigger manual sync operations
- Monitor sync history and status
- Configure data source preferences (coming soon)

### 12. Settings
- User profile management
- Preferences and configuration
- API key management options
- Data export functionality (coming soon)

## Setup & Installation

### Prerequisites
- **Python 3.13+** (`python --version`)
- **Node.js 18+** and npm (for frontend)
- **MongoDB Atlas** cluster (or local MongoDB instance)
- **Microsoft Azure AD** tenant with app registration
- **Groq API key** (primary LLM)
- **OpenAI API key** (optional, for embedding fallback)
- **Gemini API key** (optional, for embedding fallback)

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Frontend Setup

```bash
# From project root (not backend folder)
npm install
```

### Environment Configuration

Create a `.env` file in the `backend/` directory:

```ini
# ========== MICROSOFT AZURE AD ==========
AZURE_CLIENT_ID=<your_client_id_from_azure>
AZURE_CLIENT_SECRET=<your_client_secret>
AZURE_TENANT_ID=<your_tenant_id>
REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:8080

# ========== MONGODB ==========
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=work_intelligence

# ========== PRIMARY LLM (GROQ) ==========
GROQ_API_KEY=gsk_<your_groq_key>
GROQ_MODEL=qwen/qwen3-32b

# ========== EMBEDDINGS (FALLBACK TIER 1) ==========
OPENAI_API_KEY=sk-<your_openai_key>
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ========== EMBEDDINGS (FALLBACK TIER 2) ==========
GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

### Azure AD App Registration Setup

1. Go to **[Azure Portal](https://portal.azure.com)** → **Azure Active Directory** → **App registrations**
2. Click **New registration**
3. Set **Name** to `Work Intelligence Hub`
4. Set **Redirect URI** to `http://localhost:8000/auth/callback`
5. Click **Register**
6. In the app overview, copy:
   - **Application (client) ID** → `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → `AZURE_TENANT_ID`
7. Go to **Certificates & secrets** → **New client secret**
   - Copy the secret value → `AZURE_CLIENT_SECRET`
8. Go to **API permissions** → **Add a permission** → **Microsoft Graph**
9. Select **Delegated permissions** and add:
   - ✅ `User.Read` (required)
   - ✅ `Mail.Read` (for emails)
   - ✅ `Chat.Read` (for Teams chats)
   - ✅ `ChatMessage.Read` (for chat messages)
10. Click **Grant admin consent for [Tenant Name]**

### MongoDB Setup

1. Go to **[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)**
2. Create or select a project
3. Create a new cluster (free tier available)
4. Go to **Database Access** → Create a new database user
5. Go to **Network Access** → Add IP address `0.0.0.0/0` (for development)
6. Go to **Databases** → Click **Connect** on your cluster
7. Copy the **MongoDB URI** with your username/password
8. Update `MONGODB_URI` in `.env`

### Run Services

```bash
# Terminal 1 - Backend (from backend/ folder)
cd backend
.\venv\Scripts\activate  # Windows
# OR: source venv/bin/activate  # macOS/Linux
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend (from project root)
npm run dev
```

Visit **http://localhost:8080** and log in with your Microsoft account.

---

## Usage Workflow

### Step 1: Authenticate
- Navigate to http://localhost:8080
- Click **"Continue with Microsoft"**
- Grant permissions for Mail.Read and Chat.Read
- You'll be redirected to the Dashboard

### Step 2: Sync Your Data
Go to **Data Sources** tab:
1. Click **"Fetch Data"** → Retrieves raw emails/chats from Microsoft Graph
2. Click **"Process & Index"** → Chunks, embeds, and indexes into MongoDB + FAISS
3. (Optional) Click **"Sync"** → Incremental updates for new data

### Step 3: View Insights
Go to **Insights** tab to see:
- Weekly summary of your communication activity
- Key decisions identified from your emails/chats
- Risks or concerns flagged in conversations
- Trends in your work patterns

### Step 4: Ask Chat Questions
Go to **AI Chat** tab and ask:
- "How many unread mails do I have?" (fetches live count)
- "What are the key discussions this week?"
- "Summarize my recent conversations"
- Get responses with source citations from your data

### Step 5: Run AI Actions
Go to **Actions** tab and click:
- **Summarize Emails** → Overview, highlights, risks, next steps
- **Extract Tasks** → Get actionable tasks with deadlines
- **Generate Daily Report** → Executive summary, priorities, blockers

### Step 6: Manage Settings (Optional)
Go to **Settings** tab to:
- View your profile
- Configure preferences
- See sync history

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| `POST` | `/auth/login` | Redirect to Microsoft OAuth consent screen | 307 Redirect to Microsoft login |
| `GET` | `/auth/callback?code=...&state=...` | OAuth callback (handled automatically) | Sets `work_intel_access_token` cookie |
| `GET` | `/auth/me` | Get current logged-in user profile | `{id, displayName, userPrincipalName, mail}` |
| `POST` | `/auth/logout` | Log out and clear session | Clears cookie, 200 OK |

### Data Pipeline Endpoints

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| `POST` / `GET` | `/data/fetch` | Fetch raw emails/chats from Microsoft Graph (no persistence) | `{user, emails, chats, messages}` |
| `POST` | `/data/sync` | Full incremental sync: fetch → clean → chunk → embed → index | `{status, user_id, documents_saved, documents_indexed, is_incremental}` |
| `POST` | `/data/process` | Full process pipeline (non-incremental) | `{status, documents_saved, documents_indexed}` |
| `POST` | `/data/insights` | Generate AI insights from past 7 days of messages | `{weekly_summary, key_decisions, risks, trends}` |

### Chat & RAG Endpoints

| Method | Endpoint | Payload | Response |
|--------|----------|---------|----------|
| `POST` | `/chat/send` | `{message, conversation_history}` | `{status, message, conversation_history, sources}` |

### Actions Endpoints

| Method | Endpoint | Payload | Response |
|--------|----------|---------|----------|
| `POST` | `/actions/run` | `{action, context}` | `{status, result, data}` |
| `GET` | `/actions/models` | — | `{model, provider, status}` |
| `POST` | `/agent` | `{user_message, conversation_history}` | `{response, action_taken}` |

### Health & Monitoring

| Method | Endpoint | Response |
|--------|----------|----------|
| `GET` | `/health` | `{status, timestamp}` |
| `GET` | `/health/db` | `{status, connected, latency_ms}` |

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

### Messages Collection
- **Fields**: `user_id`, `source` (outlook|teams), `message_id`, `content`, `timestamp`
- **Metadata**: participants, subject, team, chunk_index, chunk_total
- **Indexes**: Unique on `(user_id, source, message_id, metadata.chunk_index)` (sparse)
- **Purpose**: Stores processed, chunked, and embedded email/chat messages

### Users Collection
- **Fields**: `user_id`, `displayName`, `mail`, `userPrincipalName`
- **Additional**: `last_sync_timestamp`, `created_at`, `updated_at`
- **Purpose**: Tracks user accounts and sync history for incremental updates

### Fetch History Collection
- **Fields**: `user`, `timestamp`, `emails_count`, `chats_count`, `total_messages`
- **Purpose**: Audit trail of data fetch operations for debugging

---

## Comprehensive Troubleshooting Guide

### ✅ Quick Diagnostics

Run these commands to check your setup:

```bash
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Check database connection
curl http://localhost:8000/health/db

# 3. Check you're logged in
curl -b "work_intel_access_token=<your-token>" http://localhost:8000/auth/me
```

### Azure AD: "Need admin approval"

**Problem**: Getting "Admin approval required" or permission denied error

**Solution**:
1. Go to Azure Portal → Azure Active Directory → App registrations → Your app
2. Click **API permissions**
3. Ensure these are added:
   - `User.Read` (required)
   - `Mail.Read` (for emails)
   - `Chat.Read` (for Teams chats)
   - `ChatMessage.Read` (for messages)
4. Click **Grant admin consent for [Tenant Name]**
5. Wait 5-10 minutes for permissions to propagate
6. Log out completely and log back in

### MongoDB: Connection Failed

**Problem**: `MongoDB connection refused` or `Authentication failed`

**Solution**:
1. Verify connection string format:
   ```
   mongodb+srv://username:password@cluster-name.mongodb.net/work_intelligence?retryWrites=true&w=majority
   ```
2. Ensure password is **URL-encoded** (e.g., `@` becomes `%40`)
3. In MongoDB Atlas, go to **Network Access** and add your IP:
   - For development: `0.0.0.0/0` (unrestricted)
   - For production: specific IP address
4. Verify username/password in **Database Access** → **Database Users**
5. Check database name matches: should be `work_intelligence`

### Chat: "Not using my data"

**Problem**: Chat responds generically without citing your emails/chats

**Solution**:
1. First, fetch data: `http://localhost:8080` → **Data Sources** → **Fetch Data**
2. Then, process: **Data Sources** → **Process & Index** (wait for completion)
3. Verify in database:
   ```bash
   # In MongoDB shell:
   db.messages.countDocuments({user_id: "<your-email>"})
   ```
4. Check FAISS index:
   - Logs should show `documents_indexed > 0`
   - If 0, re-run Process step
5. Try asking: "How many emails do I have?" (uses live data, not indexed)

### Embeddings: Falling Back to Local Hash

**Problem**: Logs show "Embedding tier 3 (local)" - embeddings are basic

**Solution**:
- Tier 1 (OpenAI) is preferred but requires API key
- Tier 2 (Gemini) is fallback
- Tier 3 (local) is last resort (non-AI)

To upgrade embeddings:
1. Add `OPENAI_API_KEY` to `.env`
2. Or add `GEMINI_API_KEY` to `.env`
3. Re-run `/data/sync` to re-embed all messages

### MongoDB E11000 Duplicate Key Error

**Problem**: `E11000 duplicate key error` when syncing

**Solution**:
```bash
# Using MongoDB shell (mongosh):
use work_intelligence
db.messages.deleteMany({source: null})
db.messages.dropIndex("uniq_user_source_message_id")
# Then re-run /data/sync in the app
```

### Token Expired: "Invalid Access Token"

**Problem**: "Invalid or expired token" error after 1 hour

**Solution**:
- Access tokens expire after ~1 hour
- Click **Logout** (top right) → **Login** again
- Or manually: `http://localhost:8000/auth/logout`

### Auth Redirect Loop

**Problem**: Stuck redirecting between login and callback

**Solution**:
1. Verify `REDIRECT_URI` in `.env`:
   ```ini
   REDIRECT_URI=http://localhost:8000/auth/callback
   ```
2. In Azure Portal → App registrations → Your app → **Authentication**:
   - Redirect URI must match exactly: `http://localhost:8000/auth/callback`
3. Clear browser cookies (open DevTools → Application → Cookies → delete `work_intel*`)
4. Restart backend: `Ctrl+C` in terminal, then `uvicorn main:app --reload`

### CORS or Backend Not Responding

**Problem**: `fetch failed`, backend endpoint returns 404

**Solution**:
1. Ensure backend is running: `uvicorn main:app --reload --port 8000`
2. Check vite.config.ts has correct proxy:
   ```typescript
   proxy: {
     '/api': 'http://localhost:8000'
   }
   ```
3. Verify frontend is calling `/api/data/...` (not `http://localhost:8000/...`)
4. Check CORS is enabled in main.py

---

## Project Structure

```
work-intelligence-hub/
│
├── backend/                          # FastAPI + Python server (port 8000)
│   ├── routes/
│   │   ├── auth.py                  # OAuth2, login, logout, profile
│   │   ├── data.py                  # Fetch, sync, process, insights
│   │   ├── chat.py                  # RAG-powered chat endpoint
│   │   └── actions.py               # AI actions: summarize, extract, report
│   │
│   ├── services/
│   │   ├── graph_api.py             # Microsoft Graph API integration
│   │   ├── processor.py             # Message processing, chunking, deduplication
│   │   ├── embedding.py             # Multi-tier embedding strategy
│   │   ├── vector_store.py          # FAISS indexing and search
│   │   ├── llm.py                   # Groq/Qwen text generation
│   │   ├── rag.py                   # RAG pipeline (embedding → search → context)
│   │   ├── gemini_actions.py        # Gemini-specific action handling
│   │   ├── gemini_chat.py           # Gemini chat integration
│   │   └── microsoft_auth.py        # Azure AD OAuth handling
│   │
│   ├── db/
│   │   └── mongodb.py               # MongoDB connection and collections
│   │
│   ├── models/
│   │   └── response_models.py       # Pydantic response schemas
│   │
│   ├── utils/
│   │   ├── settings.py              # Configuration from environment
│   │   └── mongodb.py               # MongoDB utilities
│   │
│   ├── main.py                      # FastAPI app setup, CORS, routers
│   └── requirements.txt             # Python dependencies
│
├── src/                             # React + Vite frontend (port 8080)
│   ├── pages/
│   │   ├── Login.tsx                # OAuth login page
│   │   ├── Dashboard.tsx            # Main dashboard with stats
│   │   ├── Insights.tsx             # AI-generated insights
│   │   ├── AIChat.tsx               # RAG-powered chat interface
│   │   ├── Actions.tsx              # Action execution UI
│   │   ├── DataSources.tsx          # Data sync and management
│   │   ├── SettingsPage.tsx         # User settings
│   │   ├── Index.tsx                # Home/start page
│   │   └── NotFound.tsx             # 404 page
│   │
│   ├── components/
│   │   ├── AppSidebar.tsx           # Side navigation
│   │   ├── MainLayout.tsx           # Page layout wrapper
│   │   ├── NavLink.tsx              # Navigation link component
│   │   ├── TopNavbar.tsx            # Top navigation bar
│   │   └── ui/                      # shadcn/ui components (30+ pre-built)
│   │
│   ├── hooks/
│   │   ├── use-mobile.tsx           # Responsive design hook
│   │   └── use-toast.ts             # Toast notifications hook
│   │
│   ├── lib/
│   │   └── utils.ts                 # Shared utility functions
│   │
│   ├── App.tsx                      # Main app component with routing
│   ├── main.tsx                     # React entry point
│   ├── index.css                    # Global styles
│   └── vite-env.d.ts                # Vite type definitions
│
├── public/                          # Static assets
│   └── robots.txt
│
├── Configuration Files
│   ├── package.json                 # Frontend dependencies (React, Vite, etc.)
│   ├── tsconfig.json                # TypeScript configuration
│   ├── vite.config.ts               # Vite config with API proxy
│   ├── tailwind.config.ts           # Tailwind CSS customization
│   ├── postcss.config.js            # PostCSS plugins
│   ├── eslint.config.js             # ESLint rules
│   ├── tailwind.config.ts           # Tailwind setup
│   ├── playwright.config.ts         # E2E testing config
│   ├── vitest.config.ts             # Unit test config
│   └── components.json              # shadcn/ui component registry
│
├── Documentation
│   └── README.md                    # This file
│
└── Other
    ├── bun.lockb                    # Package lock (Bun package manager)
    ├── playwright-fixture.ts        # E2E test fixtures
    └── .env.example                 # Environment variables template
```

## Stack Overview

**Frontend**
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **UI**: Tailwind CSS + shadcn/ui (30+ pre-built components)
- **Animation**: Framer Motion
- **Icons**: Lucide React

**Backend**
- **Framework**: FastAPI (Python 3.13)
- **Database**: MongoDB Atlas (cloud) or local MongoDB
- **Vector DB**: FAISS (in-memory)
- **Auth**: Microsoft OAuth 2.0 via Azure AD
- **LLM**: Groq API (Qwen model)
- **External APIs**: Microsoft Graph (Outlook, Teams Chat)

**Deployment**
- **Backend**: Uvicorn server
- **Frontend**: Vite dev server (or build to static files)
- **Database**: MongoDB Atlas (managed cloud)

---

## Roadmap

### Phase 2 (In Progress)
- ✅ Dashboard with real-time stats
- ✅ Insights generation from communication data
- ✅ Data sync with incremental updates
- ✅ RAG-powered chat with source citations
- ✅ AI actions (summarize, extract, report)
- 🔄 Multi-turn conversation memory (partially done)

### Phase 3 (Planned)
- [ ] Persistent vector DB upgrade (Pinecone or Weaviate)
- [ ] Google Workspace integration (Gmail, Google Chat)
- [ ] Calendar analytics and meeting intelligence
- [ ] Task management integration (Microsoft To Do, Todoist)
- [ ] Advanced analytics dashboard
- [ ] Custom prompt templates
- [ ] Workflow automation / Zapier integration

### Future Enhancements
- [ ] Slack integration
- [ ] Real-time notifications
- [ ] Advanced search filters
- [ ] Data export functionality
- [ ] Team collaboration features
- [ ] Mobile app

---

## Contributing

This is a proprietary project by Artesian Technologies. Contributions are welcome for bug fixes and improvements.

### Development Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Submit a pull request with description of changes
4. Code review before merge

---

## License

Proprietary — Artesian Technologies 2026

---

**Last Updated**: March 31, 2026  
**Version**: 1.0.0  
**Status**: Production-Ready  
**Author**: Artesian Technologies  
**Contact**: support@artesiantech.com
