# Quillo Agent - Replit Project

## Overview
Quillo Agent is an AI Chief of Staff orchestrator MVP with a React frontend and FastAPI backend. It provides intelligent routing, planning, and execution of high-stakes communication workflows with context awareness and continuous learning.

## Current State
- **Status**: ✅ Running in Replit environment
- **Frontend**: React + Vite + TypeScript (port 5000)
- **Backend**: FastAPI (Python 3.11, port 8000)
- **Database**: PostgreSQL (Replit-managed)
- **Last Updated**: December 20, 2025

## Project Architecture

### Frontend (`/frontend`)
- **Framework**: React 18 + Vite + TypeScript
- **Styling**: Tailwind CSS 4 + shadcn/ui components
- **Screens**: Chat, Workflows, Profile, Settings, Audit Log, Integrations
- **Port**: 5000 (Replit webview)

### Backend Core Components
1. **FastAPI Application** (`app.py`, `quillo_agent/main.py`)
   - RESTful API server with CORS support
   - Request logging middleware
   - Automatic API documentation (Swagger UI at `localhost:8000/docs`)

2. **Routers** (`quillo_agent/routers/`)
   - `/health` - Health check endpoint
   - `/route` - Intent classification (response, rewrite, argue, clarity)
   - `/plan` - Multi-step plan generation
   - `/memory/profile` - User profile management
   - `/feedback` - Feedback recording and learning

3. **Services** (`quillo_agent/services/`)
   - LLM integration (OpenRouter, Anthropic)
   - Memory management with user profiles
   - Core routing and planning logic

4. **Database** (`quillo_agent/db.py`, `quillo_agent/models.py`)
   - SQLAlchemy ORM with PostgreSQL
   - Alembic migrations for schema management
   - Models: UserProfile, FeedbackLog

### Key Features
- Rule-based intent classification with LLM fallback
- Multi-step execution planning with rationale
- Markdown-based user profiles with auto-learning
- Feedback loop for continuous improvement
- Trace IDs for debugging and analytics

## Environment Setup

### Required Dependencies
All dependencies are listed in `requirements.txt`:
- FastAPI & Uvicorn (web framework)
- Pydantic (data validation)
- SQLAlchemy & Alembic (database)
- psycopg2-binary (PostgreSQL driver)
- httpx, loguru, tenacity (utilities)

### Environment Variables
The application uses the following environment variables (configured via Replit secrets):
- `DATABASE_URL` - PostgreSQL connection (automatically set by Replit)
- `APP_ENV` - Environment (dev/prod)
- `APP_PORT` - Server port (defaults to 5000 in Replit)
- `OPENROUTER_API_KEY` - Optional for LLM features
- `ANTHROPIC_API_KEY` - Optional for LLM features
- `MODEL_ROUTING` - Model tier (fast/balanced/premium)

#### UI Authentication Token Pairing
For frontend-backend authentication via the BFF proxy layer:
- `QUILLO_UI_TOKEN` - Backend secret for validating UI requests
- `VITE_UI_TOKEN` - Frontend token (must match backend token exactly)

**Dev Mode Bypass**: When `APP_ENV=dev` and `QUILLO_UI_TOKEN` is not set, authentication is bypassed for easier development.

**Production Setup**: Both tokens must be set and match for authentication to work.

Note: The app works without LLM API keys using rule-based classification (Offline Mode).

## Running the Project

### Replit Environment (Single Combined Workflow)
The "Start Uboolia" workflow runs both servers automatically via `start-dev.sh`:

```bash
bash start-dev.sh
```

This starts:
- **Backend**: FastAPI on port 8000 (internal API)
- **Frontend**: Vite on port 5000 (webview)

The script handles graceful shutdown when you click Stop or press Ctrl+C.

### Access Points
- **Frontend UI**: Opens automatically in Replit webview (port 5000)
- **Backend API Docs**: `http://localhost:8000/docs` (internal only)
- **Health Check**: `GET http://localhost:8000/ui/api/health`
- **Auth Status**: `GET http://localhost:8000/ui/api/auth-status`

### Local Development (Outside Replit)
```bash
# Backend
pip install -r requirements.txt
alembic upgrade head
make run  # Runs on port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # Runs on port 5000
```

## API Usage Examples

### Health Check
```bash
curl https://your-repl-url.repl.co/health
```

### Route Intent
```bash
curl -X POST https://your-repl-url.repl.co/route \
  -H "Content-Type: application/json" \
  -d '{"text": "Handle this client email", "user_id": "user-123"}'
```

### Generate Plan
```bash
curl -X POST https://your-repl-url.repl.co/plan \
  -H "Content-Type: application/json" \
  -d '{"intent": "response", "user_id": "user-123", "text": "Draft reply"}'
```

## Database Management

### Migrations
Database schema is managed with Alembic:
```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### PostgreSQL Database
- Automatically provisioned by Replit
- Connection string in `DATABASE_URL` environment variable
- Tables: user_profiles, feedback_logs

## Recent Changes
- **2025-12-20**: Live/Fallback Badge for Multi-Agent Conversations
  - Added `fallback_reason` field to track why OpenRouter calls failed (timeout, rate_limited, http_error, exception, key_missing)
  - Multi-agent transcript now shows a badge above the first message: "Live" (green) when using OpenRouter, or "Fallback" (amber) for template mode
  - Fallback badge includes explanatory text and a "Retry live" button
  - Tests updated to assert fallback_reason behavior (12 tests passing)

- **2025-12-17**: UI Authentication and Auth Status Display
  - Added `/ui/api/auth/status` endpoint for debugging auth configuration
  - Implemented constant-time token comparison for security
  - Added auth status badge in UI showing: "Dev Bypass", "Auth: OK", or "Auth: Missing"
  - Fixed Vite proxy configuration for `/ui/api/*` requests
  - Dev bypass only works when `APP_ENV=dev` AND `QUILLO_UI_TOKEN` is not set
  - Added 20 comprehensive tests for all auth scenarios
  - Token pairing: `QUILLO_UI_TOKEN` (backend) and `VITE_UI_TOKEN` (frontend) must match

- **2025-12-17**: Explicit Offline vs AI-Powered mode UI
  - Added Intelligence Status badge next to Backend status (shows "AI-Powered" green or "Offline Mode" amber)
  - Badge includes tooltips explaining each mode
  - "Connect" button on Offline Mode opens modal with setup instructions for API keys
  - ExecutionResultCard now shows mode banners at top ("Offline output — template-based" or "AI-powered output — enhanced reasoning")
  - Replaced dev language: Provider→Mode, Trace ID→Result ID, Step Trace→Steps, Route Result→Classification
  - Mobile-responsive layout with flex-wrap on badges

- **2025-12-14**: Added React frontend UI
  - Imported Quillo AI Web App UI (React + Vite + TypeScript)
  - Configured dual workflows: frontend (5000) + backend (8000)
  - Added react/react-dom as dependencies
  - Configured Vite for Replit proxy compatibility
  - Frontend screens: Chat, Workflows, Profile, Settings, Audit Log, Integrations
  - API wiring not yet implemented

- **2025-11-13**: Initial Replit setup
  - Installed Python 3.11 and dependencies
  - Added psycopg2-binary for PostgreSQL support
  - Configured workflow to run on port 5000
  - Applied database migrations successfully
  - Verified all endpoints working via Swagger UI

## User Preferences
None specified yet.

## Development Notes

### Testing
Run tests with:
```bash
make test
# or
pytest -v
```

### Logs
Application logs are stored in `logs/` directory with daily rotation.

### Future Enhancements
See `QUILLO_MASTER_PLAN.md` for roadmap including:
- Real LLM tool execution
- Email integration (Gmail, Outlook)
- Analytics dashboard
- Team collaboration features
- Mobile apps

## Troubleshooting

### Common Issues
1. **Port conflicts**: The app must run on port 5000 for Replit web preview
2. **Database errors**: Ensure migrations are run with `alembic upgrade head`
3. **Missing dependencies**: Run `pip install -r requirements.txt`
4. **Import errors**: LSP may show false positives; check if app runs correctly

## Resources
- **README**: `README.md` - Comprehensive setup guide
- **API Docs**: `/docs` endpoint - Interactive API documentation
- **Master Plan**: `QUILLO_MASTER_PLAN.md` - Product roadmap
- **MVP Scope**: `QUILLO_MVP_SCOPE.md` - Current feature set
