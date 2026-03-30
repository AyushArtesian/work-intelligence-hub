# Work Intelligence Hub - Backend

A FastAPI backend for a Microsoft Graph AI Work Intelligence assistant.

- User login with Azure AD OAuth (Microsoft identity platform)
- Fetch Outlook emails, Teams chats, and chat messages via Microsoft Graph
- MongoDB (Atlas) storage for user tokens and fetch history
- CORS-enabled API for React frontend integration
- Simple auth guard and pre-built health endpoints

## Features

1. **Microsoft Authentication**
   - `GET /auth/login` redirects to Microsoft login
   - `GET /auth/callback` receives authorization code, exchanges for tokens
   - Stores user profile and tokens in `users` collection
   - Sets session cookie `work_intel_access_token`
   - `GET /auth/me` returns current user profile (requires login)
   - `POST /auth/logout` clears cookie

2. **Graph Data Fetching**
   - `GET /data/fetch` returns:
     - `user`: profile object
     - `emails`: `me/messages`
     - `chats`: `me/chats`
     - `messages`: first 1-2 chat messages per chat
   - Data fetch is token-based (use header/query token or cookie)
   - Writes fetch attempt to `fetch_history` collection

3. **MongoDB Integration**
   - `utils/mongodb.py` for DB connect + ping
   - `backend/.env` config for `MONGODB_URI`, `DATABASE_NAME`
   - robust startup behavior with warning if Mongo is unavailable

4. **Health Endpoints**
   - `GET /health` => `{"status":"ok"}`
   - `GET /health/db` => `{"status":"db_available"}` or `db_unavailable`

5. **Frontend Guard**
   - frontend `AuthGuard` checks `/auth/me` via cookie to protect `/dashboard`

## Architecture

- **Backend**: Python + FastAPI
- **Database**: MongoDB Atlas
- **Auth**: Microsoft Identity Platform (Azure AD) OAuth2
- **Graph API**: https://graph.microsoft.com/v1.0
- **Frontend**: React + Vite (separate workspace)

## Quickstart

### Prerequisites

- Python 3.11+ (`python --version`)
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

## Code structure

- `main.py` – app init, routers, CORS, startup
- `routes/auth.py` – OAuth, callback, `me`, logout
- `routes/data.py` – data fetch endpoint
- `services/microsoft_auth.py` – auth URL + token exchange
- `services/graph_api.py` – Microsoft Graph wrapper calls
- `models/response_models.py` – Pydantic response schemas
- `utils/mongodb.py` – db init + ping
- `utils/settings.py` – environment config

## Production notes

- Use HTTPS and set `secure=True` on cookie
- Replace token cookie flow with JWT if needed
- Add rate limiting and input validation
- Add background ingestion (delta sync + vector store) in Phase 2

---

### Future Phase 2 (optional)

- Data ingestion into Mongo with idempotent message upsert
- Chunking + embeddings for RAG (pgvector / Qdrant / Pinecone)
- AI endpoint (LLM prompt generation + "action engine")
- RBAC and multi-user isolation
