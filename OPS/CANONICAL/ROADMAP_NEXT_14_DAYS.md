# Roadmap: Next 14 Days

**Last updated:** 2026-01-23

## Stage A: Uorin Usable on Mobile

**Status:** DONE (merged 2026-01-18)

**Acceptance:**
- [x] Chat input visible above keyboard on iOS/Android
- [x] Messages scrollable without layout breaks
- [x] Composer has safe-area padding
- [x] Status badges compact on mobile

**Verification:** Manual test on iOS Safari + Android Chrome

---

## Stage B: Normal Mode Feels Native (CURRENT)

**Status:** IN PROGRESS

**Goal:** Normal mode must truly feel like ChatGPT/Claude/Gemini - no Work scaffolding leaking.

### Checklist

| Item | Status | Acceptance Test |
|------|--------|-----------------|
| Fix "Grok" -> "DeepSeek" in frame message | Pending | Backend returns "DeepSeek" not "Grok" |
| Remove trust contract prompts from Normal mode | Pending | Peer prompts have no "TRUST CONTRACT" text |
| Remove structured output format from Normal mode | Pending | Peers return natural text, not Evidence/Interp/Rec |
| Remove synthesis message in Normal mode | Pending | Multi-agent returns peers only, no Quillo synthesis |
| Remove "Uorin - Synthesis" label | Pending | UI shows peer names only |
| Update tooltips (no "summarize") | Pending | Tooltip says "Get second opinions" |
| Pass mode from frontend to backend | Pending | `/multi-agent` API accepts `mode` parameter |
| Backend conditionally applies trust contract | Pending | Trust contract only applied when `mode=work` |

**Verification:**
```bash
# Backend
pytest tests/test_multi_agent_*.py -v

# Frontend
npm run build
```

---

## Stage C: Minimum Distribution Loop (LATER)

**Status:** NOT STARTED

**Goal:** Known-but-private. Enable organic discovery without influencer dependency.

### Checklist

| Item | Status | Notes |
|------|--------|-------|
| Beta invite scaffolding | Pending | Request access form, invite codes |
| Email capture | Pending | Simple email input, Supabase storage |
| Share link generation | Pending | `uorin.app/invite/CODE` |
| PostHog funnel tracking | Pending | Landing -> Request -> Invited -> Active |

**NOT in scope for Stage C:**
- Influencer outreach
- Paid ads
- Public launch

---

## Prioritized Backlog (After Stage C)

1. Conversation history persistence
2. Multi-turn context in multi-agent
3. Voice input (mobile)
4. Desktop app (Tauri)
5. API rate limiting per user
6. Judgment profile v2 (inferred with confirmation)

---

## Test Commands Reference

```bash
# Full backend test
pytest

# Specific test file
pytest tests/test_multi_agent_chat.py -v

# Frontend build (type check + bundle)
npm run build

# Frontend dev
npm run dev
```
