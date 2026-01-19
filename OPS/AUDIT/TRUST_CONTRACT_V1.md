# UORIN TRUST CONTRACT v1 - Enforceable Backend Behavior

**Date:** 2026-01-11
**Status:** Implemented
**Version:** 1.0

## Overview

The UORIN TRUST CONTRACT v1 transforms Uorin from a standard AI assistant into a trust-first judgment system. This document defines the enforceable backend behaviors that implement this trust contract.

> **Mode Toggle v1 Update (2026-01-18):** Trust Contract behaviors only apply in **Work mode** (the default). In Normal mode, these guardrails are bypassed for free-form chat. See `MODE_TOGGLE_V1.md` for details.

## Core Principles

1. **Evidence Default-On**: Auto-fetch external evidence for prompts containing factual or temporal claims
2. **No Assumptions**: Ask clarifying questions when critical context is missing (never guess)
3. **Structured Outputs**: All model responses use Evidence + Interpretation + Recommendation format
4. **Preserve Disagreement**: Multi-model synthesis shows meaningful differences (no forced consensus)
5. **Clear Limitations**: State explicitly when Evidence is unavailable or limited

## Implementation

### 1. Evidence Default-On Policy

**Location:** `quillo_agent/trust_contract.py:classify_prompt_needs_evidence()`

**Triggers:** Evidence fetch is automatically triggered when user prompt contains:

#### Temporal Indicators
- Keywords: `latest`, `current`, `currently`, `recent`, `recently`, `today`, `this week/month/year`
- Specific years: `2026`, `2025`, `in 2024`, etc.
- Time references: `now`, `right now`, `updated`, `new`, `upcoming`

#### Factual/Data Indicators
- News: `news`, `headline`, `announcement`, `announced`
- Markets: `market`, `stock`, `price`, `trading`, `rate`, `inflation`, `gdp`
- Statistics: `statistics`, `data`, `numbers`, `percentage`, `percent`, `%`
- Research: `study`, `research`, `survey`, `poll`, `report`, `analysis`
- Regulatory: `law`, `regulation`, `compliance`, `policy`, `tax`, `legal`

#### Examples That Trigger Evidence
- ✅ "What are the latest UK employment law changes?"
- ✅ "Current interest rates in 2026"
- ✅ "Tesla stock price today"
- ✅ "What percentage of startups fail?"
- ✅ "Recent news about inflation"

#### Examples That Do NOT Trigger
- ❌ "Rewrite this email to sound professional" (drafting task)
- ❌ "Help me decide if I should start a business" (opinion/advice)
- ❌ "Write a thank you note" (personal content)

**Integration Points:**
- `/ui/api/ask` endpoint (quillo_agent/routers/ui_proxy.py:443)
- `/ui/api/multi-agent` endpoint (quillo_agent/routers/ui_proxy.py:624)

**Behavior:**
1. If evidence classifier returns True, automatically call `retrieve_evidence()`
2. If evidence fetch succeeds, prepend Evidence block to response
3. If evidence fetch fails/empty, state limitation clearly: "⚠️ Evidence temporarily unavailable. Response may have limited factual certainty."

### 2. No Assumptions Policy

**Location:** `quillo_agent/trust_contract.py:enforce_no_assumptions()`

**Triggers:** Questions are asked when:

#### Action Requests Without Content
- `"Rewrite this email"` → No email content provided
- `"Draft a message"` → No specifics about purpose/audience/content
- `"Analyze this document"` → No document provided

#### Decision Requests Without Criteria
- `"Should I fire this employee?"` → No context about situation/performance/criteria
- `"What should I do?"` → Vague with no decision context

#### Very Short/Vague Prompts
- `"Help"` → No indication of what help is needed
- `"Advice"` → No context for what type of advice

**Behavior:**
1. If critical context missing, return 1-3 precise questions
2. Do NOT call LLM (prevents hallucination + wasted cost)
3. Return questions with model label: `trust-contract-v1`

**Example Response:**
```
I need a few details before I can help (no guessing):

1. What specific text should I work with? Please provide the content.
2. What's the intended audience or purpose?
3. Are there specific changes or tone adjustments you want?
```

**Integration Points:**
- `/ui/api/ask` endpoint (quillo_agent/routers/ui_proxy.py:470-490)
- `/ui/api/multi-agent` endpoint (quillo_agent/routers/ui_proxy.py:656-685)

### 3. Structured Output Enforcement

**Location:** `quillo_agent/services/multi_agent_chat.py:_get_agent_prompt()`

**Format Required (All Peer Agents):**

```
**Evidence:** [Facts from provided Evidence sources, or "No Evidence provided"]
**Interpretation:** [Analysis, trade-offs, risks, considerations]
**Recommendation:** [Clear next steps with rationale]
```

**Format Required (Synthesis):**

```
**Decision Framing:** [One sentence summary]
**Key Disagreements:** [List if any, attributed; "None - agents aligned" if consensus]
**Best Move:** [Primary recommendation]
**Alternatives:** [2 options: safer and bolder]
**Evidence Note:** [State if Evidence was used or unavailable]
```

**Agent Prompts Updated:**
- Claude (quillo_agent/services/multi_agent_chat.py:46)
- DeepSeek (quillo_agent/services/multi_agent_chat.py:54)
- Gemini (quillo_agent/services/multi_agent_chat.py:62)
- Quillo Synthesis (quillo_agent/services/multi_agent_chat.py:70)

**Enforcement Method:**
- System prompts explicitly require structured format
- Models instructed: "Use ONLY Evidence provided for factual claims"
- Models instructed: "Do NOT make up facts - state uncertainty clearly"

### 4. Disagreement Preservation

**Location:** `quillo_agent/trust_contract.py:extract_disagreements()`

**Detection Logic:**
- Analyzes recommendations from all peer models
- Identifies cautious vs. bold stances using keyword heuristics
- Returns list of disagreements attributed to specific models

**Cautious Keywords:** `wait`, `careful`, `risk`, `consider`, `thorough`, `slow`
**Bold Keywords:** `act`, `now`, `immediately`, `decisive`, `move`, `commit`

**Synthesis Requirement:**
- If substantive disagreements exist, synthesis MUST list them
- Synthesis MUST NOT force false consensus
- Example: "Claude recommends caution while DeepSeek suggests immediate action"

**Integration Point:**
- Synthesis prompt in multi-agent (quillo_agent/services/multi_agent_chat.py:399)

### 5. Evidence Limitation Statements

**When Evidence Unavailable:**

The system explicitly states limitations in three scenarios:

1. **Evidence Fetch Failed:**
   - Message: "⚠️ Evidence temporarily unavailable. Response may have limited factual certainty."
   - Logged: `logger.error(f"[{trace_id}] Evidence fetch error: {e}")`

2. **Evidence Empty:**
   - Message: "⚠️ Evidence fetch attempted but no results found. Proceeding with limited factual certainty."
   - Logged: `logger.warning(f"[{trace_id}] Evidence fetch failed or empty")`

3. **Evidence Not Provided (Multi-Agent):**
   - Agents state: "**Evidence:** No Evidence provided"
   - Agents instructed: "Do NOT make up facts - state uncertainty clearly"

## Testing Coverage

**File:** `tests/test_trust_contract_v1.py`

**Test Categories (28 tests total):**

1. **Evidence Default-On (8 tests)**
   - Temporal keywords trigger (`latest`, `current`, years)
   - News/market keywords trigger
   - Statistical keywords trigger
   - Personal drafting does NOT trigger
   - Opinion questions do NOT trigger

2. **No Assumptions (8 tests)**
   - Rewrite without content triggers questions
   - Draft without context triggers questions
   - Vague prompts trigger questions
   - Decision without criteria triggers questions
   - Detailed prompts do NOT trigger
   - Factual questions do NOT trigger
   - Questions limited to max 3

3. **Output Formatting (4 tests)**
   - Model output has required structure
   - Synthesis has required structure
   - "No Evidence" stated when unavailable

4. **Disagreement Extraction (3 tests)**
   - Detects cautious vs. bold disagreements
   - Returns empty list when consensus
   - Single model has no disagreements

5. **Unstructured Parsing (2 tests)**
   - Parses sections when markers present
   - Wraps as interpretation when no markers

6. **Integration (3 tests)**
   - `/ask` endpoint triggers evidence
   - `/ask` endpoint returns questions for vague prompts
   - `/multi-agent` endpoint returns questions for vague prompts

**All 28 tests passing.**

## Known Limitations

1. **Heuristic-Based Classification**
   - Evidence classifier uses keywords, not semantic understanding
   - May miss some factual queries or over-trigger on non-factual ones
   - Improvement: Could use lightweight ML classifier in future

2. **No Conversation Memory**
   - No-assumptions checks don't have access to prior conversation turns
   - Currently assumes each prompt is standalone
   - Improvement: Integrate with conversation storage when available

3. **Structured Output Not Guaranteed**
   - Models may not always follow format instructions perfectly
   - Parser attempts to extract sections, but may fail
   - Improvement: Use structured generation APIs when available

4. **Disagreement Detection Limited**
   - Simple keyword-based heuristics for cautious vs. bold
   - May miss nuanced disagreements
   - Improvement: More sophisticated stance detection

5. **Evidence Coverage**
   - Evidence fetch uses DuckDuckGo search (limited to web results)
   - Not all factual claims can be verified via web search
   - Improvement: Add specialized data sources (APIs, databases)

## Extending the Trust Contract

### Adding New Evidence Triggers

To add new keywords that should trigger evidence fetch:

1. Edit `quillo_agent/trust_contract.py:classify_prompt_needs_evidence()`
2. Add keywords to relevant indicator list
3. Add test case in `tests/test_trust_contract_v1.py`

Example:
```python
# In trust_contract.py
temporal_indicators.append("breaking")  # Add "breaking" news

# In test_trust_contract_v1.py
def test_breaking_news_triggers_evidence():
    assert classify_prompt_needs_evidence("Breaking news about...") is True
```

### Adding New No-Assumptions Patterns

To detect new types of missing context:

1. Edit `quillo_agent/trust_contract.py:enforce_no_assumptions()`
2. Add new pattern detection logic
3. Return appropriate questions
4. Add test case

Example:
```python
# In trust_contract.py
if re.search(r'\bcompare\b.*\band\b', text_lower):
    # Comparison request without both items specified
    if len(text.split()) < 10:
        questions.append("What two things should I compare?")
        questions.append("What criteria matter most to you?")
```

### Modifying Agent Prompts

Agent prompts with structured output requirements are in:
`quillo_agent/services/multi_agent_chat.py:_get_agent_prompt()`

To change format or add new requirements:
1. Update system prompt template
2. Test with live API calls
3. Update documentation

## Rollback Procedure

A rollback tag was created before implementation:

```bash
# To rollback all changes
git checkout rollback-pre-trust-contract-v1-2026-01-11

# To create a new branch from rollback point
git checkout -b revert-trust-contract rollback-pre-trust-contract-v1-2026-01-11
```

## Operational Monitoring

**Key Metrics to Track:**

1. **Evidence Trigger Rate**
   - Log: `[{trace_id}] Evidence default-on triggered`
   - Monitor: Percentage of prompts triggering evidence
   - Expected: 20-40% of prompts (adjust heuristics if too high/low)

2. **No-Assumptions Question Rate**
   - Log: `[{trace_id}] No-assumptions triggered: {len(questions)} questions`
   - Monitor: Percentage of prompts triggering questions
   - Expected: 5-15% of prompts (adjust if too aggressive)

3. **Evidence Fetch Success Rate**
   - Log: `Evidence fetched: {len(facts)} facts from {len(sources)} sources`
   - Monitor: Percentage of evidence fetches returning results
   - Expected: 60-80% success rate

4. **Evidence Fetch Failures**
   - Log: `Evidence fetch error` / `Evidence fetch failed or empty`
   - Monitor: Count of failures by type
   - Alert: If failure rate > 40%

## References

- [Evidence Layer v1 Documentation](./EVIDENCE_LAYER_V1.md)
- [SSRF Hardening Documentation](./SSRF_HARDENING_V1.md)
- [Multi-Agent Chat Architecture](../MULTI_AGENT_CHAT.md)

## Changelog

### v1.0 (2026-01-11)
- Initial implementation of TRUST CONTRACT v1
- Evidence default-on for factual/temporal prompts
- No-assumptions enforcement with clarifying questions
- Structured outputs for multi-model responses
- Disagreement preservation in synthesis
- Clear limitation statements when evidence unavailable
- Comprehensive test coverage (28 tests)
- Integration with `/ask` and `/multi-agent` endpoints
- Documentation and operational guidelines
