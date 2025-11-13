# Quillo MVP Scope (Frozen)

## Overview
Quillo is an AI Chief of Staff orchestrator designed to handle complex communication workflows with intelligence and context awareness.

## MVP Features (Frozen)

### Core Endpoints
- **GET /health** - Health check
- **POST /route** - Intent classification with rule-based + LLM fallback
- **POST /plan** - Multi-step plan generation with rationale trace
- **GET /memory/profile** - User profile retrieval (auto-init)
- **POST /memory/profile** - User profile updates
- **POST /feedback** - Feedback loop (✅/❌) updates profile highlights

### Intent Classification
- **Intents**: response, rewrite, argue, clarity
- **Slots**: outcome (Defuse, Negotiate, Escalate)
- **Rule-based classifier** with keyword heuristics
- **LLM fallback** when confidence < 0.6 (OpenRouter/Anthropic)

### User Profile System
- **user_profile.md concept** stored in SQLite database
- Profile sections:
  - Core Identity (user editable)
  - Personal Interests (user editable)
  - Tone & Style preferences
  - Negotiation Patterns (analytics)
  - Recent Wins (user editable)
  - Active Goals (user editable)
  - Highlights (auto-appended from feedback)

### Plan Execution
- **Multi-step plans** based on intent
- **Rationale traces** explaining "why" for each step
- **Premium tier indicators** on advanced tools
- **Trace ID** for debugging and logging

### Feedback Loop
- ✅ Success / ❌ Failure recording
- Updates **Highlights** section in user profile
- Stores signals/metadata for future learning

## Tech Stack
- **Python 3.11+**
- **FastAPI** for async API
- **SQLAlchemy 2.x** + Alembic for database
- **SQLite** for MVP (Postgres-ready schema)
- **Pydantic v2** for validation
- **httpx** for async HTTP
- **loguru** for structured logging
- **tenacity** for retries
- **pytest** for testing

## Out of Scope (Post-MVP)
- Real LLM tool execution
- Multi-turn conversations
- Advanced analytics dashboard
- Team collaboration features
- Voice input/output
- Mobile apps
- Production auth (OAuth, JWT)
- Horizontal scaling
- Advanced privacy controls beyond basic profile

## Success Criteria
✅ All 5 endpoints functional
✅ Rule-based classification working
✅ Profile initialization and updates
✅ Feedback appends to profile
✅ Plan generation with rationale
✅ SQLite database with Alembic migrations
✅ Local and Replit deployment ready
✅ Basic smoke tests passing
