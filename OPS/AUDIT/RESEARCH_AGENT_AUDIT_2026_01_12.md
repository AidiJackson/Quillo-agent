# Research Agent Audit - 2026-01-12

**Branch:** audit/research-agent-v1-2026-01-12
**Checkpoint Tag:** CHECKPOINT_AUDIT_RESEARCH_AGENT_PRE_2026_01_12
**Auditor:** Claude Sonnet 4.5
**Date:** January 12, 2026

---

## Executive Summary

Uorin currently has **Evidence Layer v1** implemented - a web search + fact extraction system that uses DuckDuckGo HTML search and LLM-based fact extraction. This provides the foundation for a Research Assistant feature, but several gaps exist before reaching the intended "full Research Assistant" behavior.

**Current State:** Evidence-only (DDG snippets + LLM extraction)
**Gap to Full Research Assistant:** No full page fetching, no research pack persistence, no separate research UI

---

## 1. WHAT EXISTS TODAY (TRUTH)

### A. Evidence Retrieval System (v1)

**File:** `quillo_agent/services/evidence.py` (363 lines)

**Core Components:**

1. **Web Search Function** (`_search_web`)
   - **Line 89-141**
   - Uses DuckDuckGo HTML search (no API key required)
   - Parses search results with regex (no BeautifulSoup)
   - Returns title, URL, snippet, domain
   - **Does NOT fetch full page content** - only DDG snippets
   - Hard limit: MAX_SOURCES=8

2. **Fact Extraction Function** (`_extract_facts_from_results`)
   - **Line 144-251**
   - Uses LLM to extract neutral facts from search results
   - **Model:** `llm_router._get_openrouter_model(tier="fast")`
   - **Current model:** `anthropic/claude-3-haiku` (from config.py:23)
   - Validates facts for persuasion language (filters out "you should", "recommend", etc.)
   - Hard limit: MAX_FACTS=10
   - Returns facts with source_id, text, optional published_at date

3. **Main Entry Point** (`retrieve_evidence`)
   - **Line 254-362**
   - Coordinates search + extraction
   - Returns structured EvidenceResponse with:
     - facts: List[EvidenceFact] (max 10)
     - sources: List[EvidenceSource] (max 8)
     - retrieved_at: ISO8601 timestamp
     - duration_ms: performance metric
     - limits: optional note about empty/partial results
     - empty_reason: heuristic detection (no_results, ambiguous_query, computed_stat, etc.)

### B. API Endpoints

**File:** `quillo_agent/routers/ui_proxy.py`

1. **POST /ui/api/evidence** (Line 952-1015)
   - Manual-only evidence retrieval
   - Rate limited: 30 requests/minute
   - Auth required: X-UI-Token header
   - Payload: `{"query": "search term"}` or `{"use_last_message": true}`
   - Returns: EvidenceResponse with facts and sources

2. **Evidence Auto-Fetch in /ask** (Line 562-586)
   - Automatically fetches evidence if `classify_prompt_needs_evidence()` returns True
   - Prepends evidence block to response: `**Evidence (from web sources):**\n- fact [source]`
   - Evidence shown inline in chat response

3. **Evidence Auto-Fetch in /multi-agent** (Line 885-910)
   - Same auto-fetch logic as /ask
   - Evidence context passed to all agents
   - Evidence shown in synthesis message

### C. Evidence Classification

**File:** `quillo_agent/trust_contract.py` (Line 148+)

**Function:** `classify_prompt_needs_evidence(text: str) -> bool`

Detects if prompt needs evidence based on indicators:
- Temporal: "latest", "current", "today", "this year", "in 2026"
- News/market: "news", "market", "price", "stock", "rate"
- Statistical: "statistics", "data", "numbers", "percentage"
- Authority: "according to", "study shows", "research"
- Named entities with factual context

### D. Model Selection Infrastructure

**File:** `quillo_agent/services/llm.py` (Line 20-41)

**Class:** `LLMRouter`

**Method:** `_get_openrouter_model(tier: Optional[str], for_chat: bool) -> str`
- Accepts tier: "fast" | "balanced" | "premium"
- Maps to models from config

**File:** `quillo_agent/config.py` (Line 20-33)

**Current Model Configuration:**
```python
openrouter_fast_model: str = "anthropic/claude-3-haiku"          # Used for evidence extraction
openrouter_balanced_model: str = "anthropic/claude-3.5-sonnet"   # Default
openrouter_premium_model: str = "anthropic/claude-opus-4"        # Highest quality
openrouter_chat_model: str = "openai/gpt-4o-mini"               # Raw chat mode
openrouter_gemini_model: str = "google/gemini-2.0-flash-thinking-exp"  # Paid
openrouter_claude_agent_model: str = "anthropic/claude-3.5-sonnet"      # Multi-agent
openrouter_challenger_agent_model: str = "deepseek/deepseek-chat"       # DeepSeek V3
openrouter_gemini_agent_model: str = "google/gemini-2.5-flash"         # Multi-agent
```

**Environment Variable:** `MODEL_ROUTING=fast|balanced|premium` (defaults to "fast")

**Evidence Extraction Call** (evidence.py:194):
```python
model = llm_router._get_openrouter_model(tier="fast")  # Hardcoded to "fast" tier
```

### E. Schemas

**File:** `quillo_agent/schemas.py` (Line 158-190)

**Evidence Schemas:**
- `EvidenceFact`: text, source_id, published_at
- `EvidenceSource`: id, title, domain, url, retrieved_at
- `EvidenceRequest`: query, use_last_message
- `EvidenceResponse`: ok, retrieved_at, duration_ms, facts, sources, limits, error, empty_reason

### F. Evidence Guards (v1.1)

**File:** `quillo_agent/services/evidence.py` (Line 48-86)

**Function:** `_detect_empty_reason(query, search_results, extracted_facts) -> str`

Heuristic detection for why evidence is empty:
- `computed_stat`: Query asks for percentages/statistics (requires computation)
- `ambiguous_query`: Sports + year patterns (could mean season or calendar year)
- `source_fetch_blocked`: Got search results but no facts extracted (parsing issue)
- `no_results`: No search results at all
- `unknown`: Unclear reason

---

## 2. WHAT DOES NOT EXIST (GAPS)

### Gap 1: No Full Page Fetching
**Current:** Only uses DuckDuckGo search result snippets
**Missing:**
- Safe URL fetching with SSRF protection
- HTML parsing and content extraction
- Full article text retrieval
- PDF/document parsing

**Files That Don't Exist:**
- `quillo_agent/security/url_safety.py` - SSRF protection
- `quillo_agent/security/safe_fetch.py` - Safe HTTP fetching
- `quillo_agent/services/content_extractor.py` - Article parsing

### Gap 2: No Research Pack Persistence
**Current:** Evidence is ephemeral - generated on request, not stored
**Missing:**
- Database table for research packs
- Association with conversations/tasks
- Version history
- User annotations
- Export functionality

**No Migration Exists:** No alembic migration for research_packs table

**Missing Tables:**
- `research_packs` - Store research collections
- `research_sources` - Store fetched sources with full content
- `research_annotations` - User notes on sources

### Gap 3: No Separate Research UI
**Current:** Evidence shown inline in chat responses
**Missing:**
- Dedicated research panel/tab
- Source browsing interface
- Highlight/annotation tools
- Citation export
- Research pack management UI

### Gap 4: No Multi-Step Research Agent
**Current:** Single LLM call for fact extraction
**Missing:**
- Research planning phase (agent decides what to search)
- Iterative search refinement
- Source quality assessment
- Fact cross-referencing
- Synthesis/summarization phase

### Gap 5: No Research Model Specialization
**Current:** Uses same "fast" tier model for all evidence work
**Missing:**
- Dedicated research assistant model configuration
- Model specialization per research phase:
  - Search query generation → fast model
  - Fact extraction → balanced model
  - Synthesis/summary → premium model

---

## 3. CURRENT MODEL USAGE FOR EVIDENCE/RESEARCH

### Evidence Extraction Model

**Location:** `quillo_agent/services/evidence.py:194`

**Code:**
```python
model = llm_router._get_openrouter_model(tier="fast")
```

**Resolved To:** `anthropic/claude-3-haiku`
**Config Source:** `quillo_agent/config.py:23` → `openrouter_fast_model`

**Context:**
- Used for fact extraction from DDG snippets
- System prompt enforces neutral, non-persuasive facts
- Max tokens: 2000
- Timeout: 10 seconds

**Pricing (Approximate):**
- Claude 3 Haiku: ~$0.25/$1.25 per MTok (input/output)
- Typical evidence extraction: ~500 input tokens (snippets) + 300 output tokens (facts)
- **Cost per evidence call: ~$0.0005** (very cheap already)

### Other Model Usage Patterns

1. **Classification** (trust_contract.py): Uses `tier="fast"` → Claude 3 Haiku
2. **Multi-Agent** (multi_agent_chat.py): Uses dedicated agent models:
   - Claude: `anthropic/claude-3.5-sonnet`
   - Challenger: `deepseek/deepseek-chat` (DeepSeek V3)
   - Gemini: `google/gemini-2.5-flash`

---

## 4. CHEAPEST RESEARCH ASSISTANT MODEL RECOMMENDATION

### Recommended Model: **google/gemini-2.5-flash**

**Reasons:**
1. **Cost:** ~$0.075/$0.30 per MTok (input/output) - **70% cheaper than Claude 3 Haiku**
2. **Speed:** Very fast responses (< 2 seconds typically)
3. **Quality:** Excellent at extraction/summarization tasks
4. **Availability:** Stable on OpenRouter (not free-tier throttled)
5. **Already in use:** Used for multi-agent Gemini perspective

**Comparison Table:**

| Model | Input $/MTok | Output $/MTok | Use Case | Availability |
|-------|--------------|---------------|----------|--------------|
| **Gemini 2.5 Flash** | $0.075 | $0.30 | Research ✅ | Stable |
| Claude 3 Haiku | $0.25 | $1.25 | Current | Stable |
| GPT-4o-mini | $0.15 | $0.60 | Alternative | Stable |
| DeepSeek V3 | $0.27 | $1.10 | Alternative | Stable |

**Estimated Savings:**
- Evidence extraction: 500 input + 300 output tokens
- Current (Haiku): $0.0005/call
- Gemini 2.5 Flash: $0.00015/call
- **Savings: 70% per evidence call**

### Where to Configure It

**Primary Configuration File:** `quillo_agent/config.py`

**Option A: Override Fast Model Globally (NOT RECOMMENDED)**
```python
# Line 23
openrouter_fast_model: str = "google/gemini-2.5-flash"  # Changes ALL fast tier usage
```
**Impact:** Affects classification, evidence, and other fast-tier calls

**Option B: Add Dedicated Research Model (RECOMMENDED)**
```python
# Add new config line after line 27
openrouter_research_model: str = "google/gemini-2.5-flash"  # Dedicated for research
```

Then modify `evidence.py:194`:
```python
# OLD
model = llm_router._get_openrouter_model(tier="fast")

# NEW
model = settings.openrouter_research_model  # Use dedicated research model
```

**Option C: Environment Variable Override**
```bash
# .env file
OPENROUTER_RESEARCH_MODEL=google/gemini-2.5-flash
```

**RECOMMENDATION: Use Option B** (dedicated research model config)
- Keeps classification and other fast-tier usage unchanged
- Allows independent optimization of research vs. other tasks
- Clear separation of concerns

### Fallback Model

**Recommended Fallback:** `anthropic/claude-3-haiku` (current model)

**Fallback Logic** (to be added to evidence.py):
```python
try:
    model = settings.openrouter_research_model
except AttributeError:
    model = llm_router._get_openrouter_model(tier="fast")  # Fallback to fast tier
```

---

## 5. NEXT ATOMIC IMPLEMENTATION STEP PROPOSAL

### Recommended First Step: **Add Dedicated Research Model Configuration**

**Why This First:**
- Zero breaking changes (backward compatible)
- Immediate 70% cost savings on evidence calls
- Simple config change + one-line code edit
- Can be tested immediately with existing evidence endpoint

**Implementation Steps:**

1. **Add Config Variable** (config.py:28)
   ```python
   openrouter_research_model: str = "google/gemini-2.5-flash"
   ```

2. **Update Evidence Service** (evidence.py:194)
   ```python
   model = settings.openrouter_research_model
   ```

3. **Test Evidence Endpoint**
   ```bash
   curl -X POST http://localhost:8000/ui/api/evidence \
     -H "X-UI-Token: demo-token-2025" \
     -H "Content-Type: application/json" \
     -d '{"query": "Python 3.12 release date"}'
   ```

4. **Verify Cost Savings**
   - Check OpenRouter dashboard for model usage
   - Confirm Gemini 2.5 Flash is being used
   - Monitor for quality degradation (should be minimal)

**Alternative First Step (More Ambitious):** **Research Pack v1 Persistence**

If cost savings is not priority, consider implementing research pack storage:
1. Add alembic migration for research_packs table
2. Store evidence responses in DB
3. Associate with conversation_id or task_id
4. Add GET /ui/api/research-packs endpoint
5. Allow viewing saved research separately from chat

**Time Estimate:** 3-4 hours vs. 15 minutes for model config change

---

## 6. DETAILED FILE MAP

### Core Evidence Files
- `quillo_agent/services/evidence.py` (363 lines) - Main evidence service
- `quillo_agent/services/llm.py` (400+ lines) - LLM router and chat interface
- `quillo_agent/routers/ui_proxy.py` (1200+ lines) - API endpoints
- `quillo_agent/schemas.py` (255+ lines) - Pydantic models
- `quillo_agent/trust_contract.py` (200+ lines) - Evidence classification logic
- `quillo_agent/config.py` (91 lines) - Configuration settings

### Model Selection Hooks
- **Config:** `quillo_agent/config.py:23` - `openrouter_fast_model`
- **Router:** `quillo_agent/services/llm.py:20` - `_get_openrouter_model()`
- **Usage:** `quillo_agent/services/evidence.py:194` - Evidence extraction call

### Evidence Auto-Fetch Integration
- **Classifier:** `quillo_agent/trust_contract.py:148` - `classify_prompt_needs_evidence()`
- **Ask Endpoint:** `quillo_agent/routers/ui_proxy.py:562` - Auto-fetch in /ask
- **Multi-Agent:** `quillo_agent/routers/ui_proxy.py:885` - Auto-fetch in /multi-agent

### Missing Files (Gaps)
- `quillo_agent/security/url_safety.py` - SSRF protection ❌
- `quillo_agent/security/safe_fetch.py` - Safe HTTP fetching ❌
- `quillo_agent/services/content_extractor.py` - Article parsing ❌
- `quillo_agent/services/research_pack.py` - Research pack management ❌
- `alembic/versions/XXXX_add_research_packs.py` - Persistence migration ❌

---

## 7. SUMMARY

### What Works Today
✅ DuckDuckGo HTML search (no API key required)
✅ LLM-based fact extraction with persuasion filtering
✅ Structured evidence response with sources and timestamps
✅ Manual evidence endpoint (POST /evidence)
✅ Auto-fetch evidence in /ask and /multi-agent
✅ Evidence classification heuristics
✅ Empty result detection with reason codes

### What's Missing
❌ Full page content fetching (only has DDG snippets)
❌ SSRF protection and safe URL fetching
❌ Research pack persistence (DB storage)
❌ Separate research UI (inline chat only)
❌ Multi-step research agent (single LLM call only)
❌ Dedicated research model configuration

### Cost Optimization Opportunity
💰 **Current:** Claude 3 Haiku ($0.25/$1.25 per MTok)
💰 **Recommended:** Gemini 2.5 Flash ($0.075/$0.30 per MTok)
💰 **Savings:** 70% cost reduction per evidence call

### Recommended Next Step
🎯 **Add dedicated research model config** (15 min implementation)
🎯 **Alternative:** Implement Research Pack v1 persistence (3-4 hours)

---

## 8. VERIFICATION COMMANDS

### Test Evidence Service Locally

```bash
# 1. Ensure server is running
curl http://localhost:8000/ui/api/health

# 2. Test evidence endpoint (requires auth token from .env)
curl -X POST http://localhost:8000/ui/api/evidence \
  -H "X-UI-Token: $(grep QUILLO_UI_TOKEN .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python 3.12 new features"}'

# 3. Check model usage
# Look for "anthropic/claude-3-haiku" in logs
tail -f logs/quillo_*.log | grep "openrouter"

# 4. Test auto-fetch in /ask
curl -X POST http://localhost:8000/ui/api/ask \
  -H "X-UI-Token: $(grep QUILLO_UI_TOKEN .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the latest Python 3.12 features?"}'
```

### Check Configuration

```bash
# View current model config
grep "openrouter.*model" quillo_agent/config.py

# Check evidence service model usage
grep "_get_openrouter_model" quillo_agent/services/evidence.py

# Verify no research model config exists yet
grep "research_model" quillo_agent/config.py || echo "Not found (expected)"
```

---

## Audit Complete

**Branch:** audit/research-agent-v1-2026-01-12
**Tag:** CHECKPOINT_AUDIT_RESEARCH_AGENT_PRE_2026_01_12
**Next Action:** Review recommendations and choose implementation path
