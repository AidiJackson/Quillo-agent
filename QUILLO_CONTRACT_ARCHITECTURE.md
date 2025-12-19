# UBOOLIA — Quillo Architecture Contract (v1)

**Status:** Locked v1 (read-only contract)
**Scope:** Defines how "Quillo" (name subject to change) fits into Uboolia and how it interacts with suites/tools.

---

## 1) What exists today (and stays separate)

### A) Uboolia Tool Suite (separate, first-class)
- **Response**
- **Rewrite**
- **Argue**
- **Clarity**

Users can run these tools directly at any time.
These remain **standalone** and **first-class**.

### B) Quillo (soon to be renamed)
Quillo is a separate app/suite with a **chat-first UI** and also appears as an **overlay** inside every suite.

Quillo is not "a tool". Quillo is the **orchestrator** (judgment layer + planning + execution + explanation).

---

## 2) Core contract (the spine)

Quillo always follows this pipeline:

**Conversation → Judgment → (optional) Plan → (optional) Execute → Explain**

- **Conversation**: user talks to Quillo in a ChatGPT-like experience.
- **Judgment**: determine stakes + whether confirmation is required.
- **Plan**: produce a visible workflow (tool steps).
- **Execute**: run the steps (default: safe / dry-run unless permitted).
- **Explain**: summarize what happened, what changed, and next recommended action.

---

## 3) Judgment Layer (gatekeeper)

The Judgment Layer is the single source of truth for:
- stakes: `low | medium | high`
- what_i_see
- why_it_matters (omitted for low stakes)
- recommendation
- requires_confirmation: `true | false`

Judgment must run:
- on every user message (chat-first feel)
- before planning
- before executing
- before any external action (now or future: sending emails, CRM updates, scheduling, etc.)

---

## 4) Runtime flow (end-to-end)

### A) Chat-first default (always)
1. User sends message → `POST /ui/api/judgment`
2. UI renders Quillo reply + stakes badge
3. If stakes are low: Quillo may suggest a workflow and offer action buttons
4. If stakes are medium/high: Quillo requests confirmation ("Proceed / Not yet")

### B) Planning (only when allowed)
5. If user clicks Proceed (or autonomy permits): `POST /ui/api/plan`
6. UI shows **Workflow panel** (steps, friendly tool names, premium markers)

### C) Execution (only when allowed)
7. `POST /ui/api/execute` (default: dry-run unless explicitly permitted)
8. UI shows execution artifacts + step trace
9. Quillo summarizes outcome + recommended next action

---

## 5) How Quillo "uses tools" while tools remain separate

Quillo does not "click UI buttons."

Suites expose tools as **capabilities**, via a stable internal contract:

### Tool Capability Contract
- `tool_id`: `response | rewrite | argue | clarity | ...`
- `input_schema`: required inputs
- `output_schema`: returned outputs/artifacts
- `cost_tier`: free / pro / premium
- `safety_flags`: e.g. `external_action`, `requires_review`

Quillo calls capabilities.
Each suite may optionally **visualize** those calls so the user can "watch Quillo run the tools."

---

## 6) Plug-in model across suites (Quillo everywhere)

Every suite implements the same overlay/dock pattern:

### Quillo Dock (Overlay Component)
- Opens a chat panel (message box is primary)
- Can expand Workflow panel, Profile, Settings
- Uses the same backend routes (`/ui/api/*`)
- Receives the suite's available capability list

This means:
- In the Tool Suite: Quillo can run Response/Rewrite/Argue/Clarity.
- In future suites: Quillo can run those suite tools via capabilities.
- Same Quillo brain, different capability surface.

---

## 7) Autonomy + permissions model (always ask first)

Default behavior: **always ask first**.

### Action Permission Levels
- **Level 0:** Always ask (default)
- **Level 1:** Ask once per workflow (batch approval)
- **Level 2:** Autopilot for low/medium stakes only
- **Level 3:** Full autopilot (admin / enterprise-only)

Rules:
- If `requires_confirmation=true`, Quillo must request explicit approval unless Level 3.
- Any `external_action` capability requires stronger permission than internal-only actions.

---

## 8) Multi-agent "group chat" mode (controlled)

Group chat is allowed, but must be moderator-controlled to avoid chaos.

### Group Chat Mode Contract
- Quillo remains the Moderator.
- Additional agents join as **advisors** (each mapped to a provider/model).
- Quillo synthesizes opinions into one final recommendation.
- UI can optionally reveal "second opinions" behind an expandable panel.

---

## 9) Naming (renaming Quillo is safe)

"Quillo" is a UI/brand label and can be renamed without breaking architecture.

The real locked primitives are:
- Judgment Layer gatekeeping
- Capability contract per suite
- Quillo Dock overlay
- Permission model
- Plan/Execute pipelines

---

## 10) v1 outcomes (what users should feel)

- Quillo feels like a premium ChatGPT-level assistant that understands stakes.
- Users can still use tools directly, but Quillo can run them better and faster.
- Workflows are visible when helpful and hidden when not.
- The platform's differentiator is **judgment under pressure**, not "writing."

---

END OF DOCUMENT
