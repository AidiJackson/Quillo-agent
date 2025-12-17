# Quillo Agent 🎯

**AI Chief of Staff orchestrator - MVP**

Quillo is a production-quality FastAPI microservice that intelligently routes, plans, and executes high-stakes communication workflows with context awareness and continuous learning.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip and venv

### Local Setup

```bash
# 1. Clone the repository (if not already)
git clone <your-repo-url>
cd Quillo-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys (optional for MVP)

# 5. Run database migrations
make migrate

# 6. Start the server
make run
```

Server will be available at `http://localhost:8000`

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/route` | POST | Intent classification (response, rewrite, argue, clarity) |
| `/plan` | POST | Multi-step plan generation with rationale |
| `/memory/profile` | GET | Retrieve user profile (auto-initializes) |
| `/memory/profile` | POST | Update user profile |
| `/feedback` | POST | Record feedback (✅/❌) and update profile |
| `/ask` | POST | Get business advice from Quillopreneur specialist |

### API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔐 Authentication

### Backend API Authentication (Server-to-Server)

All backend API endpoints under `/route`, `/plan`, `/ask`, `/memory`, `/feedback` require authentication using an API key.

**Setting Up Your API Key:**

1. Generate a secure API key (recommended: use a password manager or `openssl rand -hex 32`)
2. Add it to your `.env` file:
   ```bash
   QUILLO_API_KEY=your-secret-api-key-here
   ```
3. Include the API key in the `Authorization` header for all requests:
   ```
   Authorization: Bearer your-secret-api-key-here
   ```

### Frontend Security (UI Proxy / BFF)

**Important: The frontend NEVER stores or sends API keys.**

To prevent API key exposure in the browser, Quillo uses a **Backend-For-Frontend (BFF) proxy** pattern:

- **Frontend calls**: `/ui/api/*` endpoints (no API key required)
- **BFF proxy**: Server-side router validates UI token and calls internal services
- **Security features**:
  - Rate limiting (30 requests/min per IP for /route, /plan, /ask)
  - UI token authentication (X-UI-Token header)
  - Direct service calls (no HTTP overhead)

**UI Token Setup (Dev-Only):**

1. Add UI token to backend `.env`:
   ```bash
   QUILLO_UI_TOKEN=dev-ui-token-12345
   ```
2. Add UI token to frontend `.env`:
   ```bash
   VITE_UI_TOKEN=dev-ui-token-12345
   ```

**Production Recommendation:**
- Replace `QUILLO_UI_TOKEN` with session-based authentication
- Use HTTP-only cookies for session management
- Implement proper user authentication (OAuth, JWT, etc.)

### Unauthenticated Access

- ❌ Backend API requests without `Authorization` header → `401 Unauthorized`
- ❌ UI proxy requests without `X-UI-Token` header → `401 Unauthorized` (unless dev mode with no token set)
- ✅ The `/health` and `/ui/api/health` endpoints do not require authentication

---

## 🧪 Sample API Calls

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok"}
```

---

### 2. Route Intent
```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-api-key-here" \
  -d '{
    "text": "Handle this client email and defuse conflict",
    "user_id": "demo-user-123"
  }'
```

**Response:**
```json
{
  "intent": "response",
  "reasons": [
    "Detected response keywords (handle/respond/reply/answer/client/email)",
    "Extracted outcome slot: Defuse"
  ],
  "slots": {
    "outcome": "Defuse"
  }
}
```

---

### 3. Generate Plan
```bash
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-api-key-here" \
  -d '{
    "intent": "response",
    "user_id": "demo-user-123",
    "slots": {"outcome": "Defuse"},
    "text": "Handle this client email and defuse conflict"
  }'
```

**Response:**
```json
{
  "steps": [
    {
      "tool": "response_generator",
      "premium": false,
      "rationale": "Generate initial response based on user profile and context"
    },
    {
      "tool": "tone_adjuster",
      "premium": true,
      "rationale": "Adjust tone to match user preferences and situation urgency"
    },
    {
      "tool": "conflict_resolver",
      "premium": true,
      "rationale": "Apply de-escalation techniques to defuse conflict"
    }
  ],
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### 4. Ask Quillopreneur for Business Advice
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-api-key-here" \
  -d '{
    "text": "How should I price my SaaS product?",
    "user_id": "demo-user-123"
  }'
```

**Response:**
```json
{
  "answer": "When pricing a SaaS product, consider these key factors:\n\n1. **Value-based pricing**: Base your price on the value you deliver to customers, not just your costs...",
  "model": "claude-3-5-sonnet-20241022",
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Notes:**
- The `user_id` is optional. If provided, user profile context will be included for personalized advice.
- If no API keys are configured, returns offline template response with `model: "offline"`.
- Model selection respects `MODEL_ROUTING` setting (fast/balanced/premium).

---

### 5. Get User Profile
```bash
curl "http://localhost:8000/memory/profile?user_id=demo-user-123"
```

**Response:**
```json
{
  "profile_md": "# User Profile: demo-user-123\n\n## Core Identity\n(user editable)...",
  "updated_at": "2025-01-10T12:34:56.789000"
}
```

---

### 5. Record Feedback
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-123",
    "tool": "response_generator",
    "outcome": true,
    "signals": {"confidence": 0.95}
  }'
```

**Response:**
```json
{"ok": true}
```

---

## 🧰 Development Commands

### Makefile Targets

```bash
# Run the application
make run

# Run database migrations
make migrate

# Create a new migration
make revision MSG="add new table"

# Run tests
make test

# Install dependencies
make install

# Full setup (install + migrate + logs)
make setup

# Clean up generated files
make clean
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_health.py -v

# Run with coverage
pytest --cov=quillo_agent tests/
```

---

## 🗄️ Database

### SQLite (Default for MVP)
- Database file: `quillo.db` (created on first migration)
- Migrations: Alembic in `alembic/versions/`

### Postgres (Production-Ready)
To switch to Postgres, update `.env`:
```bash
DATABASE_URL=postgresql://user:password@localhost/quillo
```

---

## 📦 Deployment

### Replit

1. **Import Repository**:
   - Go to [Replit](https://replit.com)
   - Click "Create Repl" → "Import from GitHub"
   - Paste your repo URL

2. **Configure Environment**:
   - Open "Secrets" (lock icon)
   - Add environment variables from `.env.example`

3. **Run Setup**:
   ```bash
   pip install -r requirements.txt
   make migrate
   ```

4. **Start Server**:
   - Click "Run" or execute `make run`
   - Replit will provide a public URL

### Railway / Render

1. **Connect Repository**:
   - Link your GitHub repo
   - Set environment variables in dashboard

2. **Configure Build**:
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Deploy**:
   - Push to main branch → auto-deploys

---

## 🔐 Environment Variables

Create a `.env` file from `.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/prod) | `dev` |
| `APP_PORT` | Server port | `8000` |
| `DATABASE_URL` | Database connection string | `sqlite:///./quillo.db` |
| **OpenRouter Provider** | | |
| `OPENROUTER_API_KEY` | OpenRouter API key (optional) | - |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_FAST_MODEL` | Fast model for quick tasks | `anthropic/claude-3-haiku` |
| `OPENROUTER_BALANCED_MODEL` | Balanced model for general use | `anthropic/claude-3.5-sonnet` |
| `OPENROUTER_PREMIUM_MODEL` | Premium model for complex reasoning | `anthropic/claude-opus-4` |
| **Anthropic Provider (Direct)** | | |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional, fallback) | - |
| **Model Routing** | | |
| `MODEL_ROUTING` | Model tier (fast/balanced/premium) | `fast` |
| **Security** | | |
| `QUILLO_API_KEY` | Server-side API key for backend endpoints | - |
| `QUILLO_UI_TOKEN` | UI token for frontend proxy (dev-only) | - |

**Note**: API keys are optional for MVP. Rule-based classification works without them.

### 🤖 Configuring OpenRouter

OpenRouter is the preferred LLM provider for Quillo, offering access to multiple AI models through a unified API.

#### Setup Steps:

1. **Get an API key** from [OpenRouter](https://openrouter.ai)
2. **Add to `.env`**:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
3. **Choose your routing tier**:
   ```bash
   MODEL_ROUTING=fast      # Cost-optimized (Haiku)
   MODEL_ROUTING=balanced  # Best balance (Sonnet)
   MODEL_ROUTING=premium   # Advanced reasoning (Opus)
   ```

#### Model Routing Behavior:

- **`/route`**: Uses fast model for LLM fallback when rule-based confidence < 0.6
- **`/plan`**: Uses premium model when `MODEL_ROUTING=premium`, otherwise deterministic
- **`/ask`**: Uses model tier specified by `MODEL_ROUTING`

#### Example: Testing Model Routing

```bash
# Fast mode - uses claude-3-haiku for cost efficiency
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How should I price my SaaS product?",
    "user_id": "demo-user"
  }'

# Response includes model used:
# {"answer": "...", "model": "openrouter/anthropic/claude-3-haiku", "trace_id": "..."}
```

#### Custom Models:

You can override default models in `.env`:
```bash
OPENROUTER_FAST_MODEL=openai/gpt-3.5-turbo
OPENROUTER_BALANCED_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_PREMIUM_MODEL=anthropic/claude-opus-4
```

See [OpenRouter Models](https://openrouter.ai/models) for available options.

#### Fallback Chain:

1. **OpenRouter** (if `OPENROUTER_API_KEY` is set)
2. **Anthropic Direct** (if `ANTHROPIC_API_KEY` is set)
3. **Offline Mode** (rule-based classification + template responses)

---

## 📚 Documentation

- **[QUILLO_MVP_SCOPE.md](QUILLO_MVP_SCOPE.md)**: Frozen MVP features and scope
- **[QUILLO_MASTER_PLAN.md](QUILLO_MASTER_PLAN.md)**: Roadmap and phases
- **[QUILLO_PITCH_DECK_CUSTOMER.md](QUILLO_PITCH_DECK_CUSTOMER.md)**: Customer pitch deck
- **[PRICING_LADDER.md](PRICING_LADDER.md)**: Pricing tiers and structure
- **[docs/UI_BRIEF_FIGMA.md](docs/UI_BRIEF_FIGMA.md)**: UI design specifications
- **[docs/FRAMER_INTEGRATION.md](docs/FRAMER_INTEGRATION.md)**: Framer frontend integration guide

---

## 🏗️ Project Structure

```
.
├── app.py                      # FastAPI entrypoint
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── Makefile                    # Common development tasks
├── README.md                   # This file
├── quillo_agent/               # Main application package
│   ├── __init__.py
│   ├── main.py                 # FastAPI app creation
│   ├── config.py               # Settings management
│   ├── db.py                   # Database setup
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── routers/                # API route handlers
│   │   ├── health.py
│   │   ├── route.py
│   │   ├── plan.py
│   │   ├── memory.py
│   │   └── feedback.py
│   ├── services/               # Business logic
│   │   ├── llm.py              # LLM integration
│   │   ├── memory.py           # Profile & feedback
│   │   └── quillo.py           # Core routing & planning
│   └── utils/                  # Helper utilities
│       ├── classifier.py       # Rule-based classifier
│       └── explain.py          # Rationale generation
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py
├── tests/                      # Pytest tests
│   ├── test_health.py
│   └── test_route_plan.py
└── docs/                       # Additional documentation
    ├── UI_BRIEF_FIGMA.md
    └── FRAMER_INTEGRATION.md
```

---

## 🎯 Core Features

### ✅ Intent Classification
- **Rule-based** keyword heuristics for speed
- **LLM fallback** when confidence < 0.6
- **Intents**: response, rewrite, argue, clarity
- **Slots**: outcome (Defuse, Negotiate, Escalate)

### ✅ Plan Generation
- Multi-step execution plans with rationale
- Premium tool indicators
- Trace IDs for debugging

### ✅ User Profile System
- Markdown-based profiles stored in database
- Auto-initialization on first access
- Editable by user
- Auto-learning from feedback

### ✅ Feedback Loop
- ✅/❌ outcome recording
- Appends highlights to profile
- Stores signals for future learning

---

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'quillo_agent'`
**Solution**: Ensure you're running from the project root and have activated the venv:
```bash
cd Quillo-agent
source venv/bin/activate
python -m pytest tests/
```

### Issue: Database errors
**Solution**: Run migrations:
```bash
make migrate
```

### Issue: Port already in use
**Solution**: Change port in `.env` or use:
```bash
APP_PORT=8001 make run
```

### Issue: Tests failing
**Solution**: Ensure database is migrated and logs directory exists:
```bash
make setup
make test
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 📧 Contact

- **Email**: hello@quillo.ai
- **GitHub**: [Quillo-agent](https://github.com/yourusername/Quillo-agent)
- **Twitter**: @quilloai

---

## 🎉 What's Next?

After MVP:
- [ ] Real LLM tool execution
- [ ] Email integration (Gmail, Outlook)
- [ ] Analytics dashboard
- [ ] Team collaboration features
- [ ] Mobile apps
- [ ] Production auth (OAuth, JWT)

See [QUILLO_MASTER_PLAN.md](QUILLO_MASTER_PLAN.md) for full roadmap.

---

**Built with ❤️ by the Quillo team**