# DO NOT BREAK - Uorin Operating System

**Last updated:** 2026-01-23

## Product Identity (Locked)

Uorin is a multi-model judgment chat with execution tools. It is **not** a writing assistant or advisor bot.

**Positioning:** Known but private. Product first. Minimal founder exposure.

---

## Mode Contract (Non-Negotiable)

| Mode | Behavior | Enforcement |
|------|----------|-------------|
| **Normal** | Raw, natural, unrestricted. Feels like native ChatGPT/Claude/Gemini/DeepSeek. No scaffolding. | NO trust contract prompts. NO structured output format. NO synthesis labels. NO micro-disclosures. |
| **Work** | Judgment-first. Guardrails, evidence triggers, stress test, structured outputs. | Trust contract enforced. Synthesis block. Lens assignments. Evidence default-on for factual queries. |

### Normal Mode Parity Rules

1. Peer agents reply naturally (no "TRUST CONTRACT" prompts)
2. No synthesis message - just show peer replies
3. No "Uorin - Synthesis" labels
4. Tooltips say "Get second opinions" not "Uorin will summarize"
5. No structured output format (Evidence/Interpretation/Recommendation)

### Work Mode May Include

- Trust contract enforcement
- Structured outputs
- Stress test mode (consequence-detected)
- Evidence auto-fetch for factual queries
- Synthesis with lens assignments

---

## Trust Principles (Non-Negotiable)

1. **No silent learning** - Uorin never infers preferences without explicit confirmation
2. **Profile only explicit** - All stored preferences have `source=explicit` and `confirmed_at` timestamp
3. **Self-explanation never lies** - Transparency card reflects actual state

---

## Never Again Rules

1. **Always checkpoint first** - Create branch + annotated tag before any change session
2. **Always ship in atomic PRs** - No mega PRs. Each PR does one thing, reversibly.
3. **No changing workflow mid-session** - Follow the locked workflow, don't improvise
4. **Test before merge** - `pytest` + `npm run build` must pass

---

## Rollback Protocol

```bash
# View available rollback points
git tag | grep ROLLBACK

# Reset to rollback point
git reset --hard ROLLBACK_<TAG_NAME>
git push -f origin <branch>  # Only if force-push is approved
```

---

## Files That Define Truth

| File | Purpose |
|------|---------|
| `OPS/CANONICAL/DO_NOT_BREAK.md` | This file - operating rules |
| `OPS/CANONICAL/UORIN_PRODUCT_SPEC.md` | Product spec - what Uorin is/isn't |
| `OPS/CANONICAL/ROADMAP_NEXT_14_DAYS.md` | Current sprint priorities |
| `frontend/src/lib/uorinMode.ts` | Mode state (Normal/Work) |
| `quillo_agent/services/multi_agent_chat.py` | Multi-agent behavior |
| `quillo_agent/trust_contract.py` | Work mode enforcement logic |
