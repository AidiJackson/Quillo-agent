# Quillo Agent - Replit Project

## Overview
Quillo Agent is an AI Chief of Staff orchestrator MVP built with FastAPI. It provides intelligent routing, planning, and execution of high-stakes communication workflows with context awareness and continuous learning.

## Current State
- **Status**: ✅ Running in Replit environment
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (Replit-managed)
- **Port**: 5000
- **Last Updated**: November 13, 2025

## Project Architecture

### Core Components
1. **FastAPI Application** (`app.py`, `quillo_agent/main.py`)
   - RESTful API server with CORS support
   - Request logging middleware
   - Automatic API documentation (Swagger UI at `/docs`)

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

Note: The app works without API keys using rule-based classification.

## Running the Project

### Local Development (Outside Replit)
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
make run
```

### Replit Environment
The workflow is configured to automatically run:
```bash
uvicorn app:app --host 0.0.0.0 --port 5000
```

Access the API:
- **Web Preview**: Opens automatically in Replit
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **Health Check**: `GET /health`

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
