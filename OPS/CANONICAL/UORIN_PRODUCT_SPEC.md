# Uorin Product Spec

**Last updated:** 2026-01-23

## What Uorin Is

Multi-model judgment chat with execution tools.

- **Chat:** Conversational interface to multiple AI models (Claude, DeepSeek, Gemini, GPT-4o)
- **Judgment:** Stakes assessment, consequence detection, structured analysis (Work mode only)
- **Execution:** QuilloConnect 4 tools (Response, Rewrite, Argument, Clarity)

## What Uorin Is Not

- Not a writing assistant
- Not an advisor bot
- Not a ChatGPT clone (even in Normal mode - we enable multi-model, not single-model)
- Not a workflow automation tool

---

## Two-Mode Behavior Table

| Feature | Normal Mode | Work Mode |
|---------|-------------|-----------|
| **Single chat** | Raw LLM response via `/ask` | Judgment layer via `/judgment` |
| **Multi-agent** | Peer replies only (Claude, DeepSeek, Gemini) | Peers + Uorin synthesis |
| **Evidence** | Manual only (`/evidence` or button) | Auto-fetch for factual/temporal queries |
| **Stress test** | Never | Auto-triggered on consequence detection |
| **Trust contract prompts** | Never | Always |
| **Structured outputs** | Never | Evidence/Interpretation/Recommendation |
| **Lens assignments** | Never | Risk/Relationship/Strategy/Execution |
| **Micro-disclosures** | Never | When relevant context is used |
| **Self-explanation card** | On request | On request |
| **Task approval settings** | Hidden | Visible |

---

## Evidence Layer Behavior

| Mode | Auto-fetch | Manual fetch | Interpretation |
|------|------------|--------------|----------------|
| Normal | No | Yes (button/command) | Only if facts found |
| Work | Yes (if factual query detected) | Yes | Only if facts found |

**Evidence Guards (both modes):**
- If no facts found: disable interpretation, show refine suggestions
- Facts always have source + timestamp
- No authorial speculation on empty evidence

---

## Multi-Agent Behavior Differences

### Normal Mode

```
User: "Should I quit my job?"

Claude: [raw response]
DeepSeek: [raw response]
Gemini: [raw response]

(No synthesis. No Uorin message after peers.)
```

### Work Mode

```
User: "Should I quit my job?"

Quillo (frame): "Let me bring in perspectives..."

Claude (Risk lens): [structured Evidence/Interpretation/Recommendation]
DeepSeek (Relationship lens): [structured]
Gemini (Strategy lens): [structured]

Quillo (synthesis):
- Decision Framing: ...
- Top Risks: ...
- Key Disagreements: ...
- Best Move: ...
- Alternatives: ...
- Execution Tool: ...
- Evidence Note: ...
```

---

## API Endpoints

| Endpoint | Normal Mode | Work Mode |
|----------|-------------|-----------|
| `POST /ask` | Primary chat | Not used |
| `POST /judgment` | Not used | Primary chat |
| `POST /multi-agent` | Peers only | Peers + synthesis |
| `POST /evidence` | Manual | Auto + Manual |
| `GET /config` | Returns `raw_chat_mode: true` | N/A (mode stored client-side) |

---

## UI Components

| Component | Normal Mode | Work Mode |
|-----------|-------------|-----------|
| Mode toggle | Visible (Settings) | Visible (Settings) |
| Task Approval settings | Hidden | Visible |
| Advanced Task-Specific Models | Hidden | Visible |
| Judgment Profile | Visible | Visible |
| Evidence button | Visible | Visible |
| Multi-agent button | Visible | Visible |
| Workflow panel | Hidden | Visible (on Proceed) |
