# STRESS TEST v1 - Automatic Consequence-Detected Mode

**Date:** 2026-01-11
**Status:** Implemented
**Version:** 1.0
**Built On:** UORIN TRUST CONTRACT v1

## Overview

STRESS TEST v1 is an automatic, consequence-detected mode that activates when a user's prompt implies decision-making or consequence evaluation. It builds on top of the UORIN TRUST CONTRACT v1, preserving all trust-first behaviors while adding specialized lens-based analysis when high-stakes decisions are detected.

**Key Principle:** Free-form chat is preserved when consequence is NOT detected. Stress Test only activates for genuinely consequential prompts.

## Core Behavior

**Normal Mode (No Consequence Detected):**
- Multi-agent chat operates as usual with Trust Contract protections
- Agents provide general perspectives
- Casual, informational, and drafting requests flow through normally

**Stress Test Mode (Consequence Detected):**
- Each model receives a specialized lens assignment
- Synthesis gets Execution Lens for clarity and actionability
- All Trust Contract protections remain active (Evidence, No Assumptions, etc.)

## Implementation

### 1. Consequence Detection

**Location:** `quillo_agent/trust_contract.py:detect_consequence()`

**Triggers:** Stress Test mode activates when user prompt contains decision/consequence signals:

#### "Should I" Questions
- `"Should I fire this employee?"`
- `"Should I send this email to the client?"`
- `"Should we launch the product now?"`

#### Decision Framing
- `"What's the best move here?"`
- `"Is it worth investing in this?"`
- `"I need a second opinion on this decision"`
- `"What would you do in my situation?"`

#### Risk/Consequence Framing
- `"Is this too risky to proceed?"`
- `"What are the legal consequences?"`
- `"Could this damage our relationship with the client?"`
- `"What's the fallout if this goes wrong?"`

#### Irreversible Actions
- `"Should I terminate the contract?"`
- `"Ready to publish this announcement"`
- `"Should I resign from my position?"`
- `"About to sue the vendor"`

#### Action Verbs (with word boundaries)
- Keywords: `fire`, `hire`, `escalate`, `approve`, `terminate`, `resign`, `sue`, `end`, `sign`, `file`, `quit`, `cancel`, `delete`, `remove`
- Example: `"Should I hire this candidate?"`
- Example: `"Do I escalate this to management?"`

#### Examples That Trigger Stress Test
- ✅ "Should I fire this underperforming manager?"
- ✅ "What's the best move for handling this legal dispute?"
- ✅ "Is it too risky to invest in this startup?"
- ✅ "Should I terminate the vendor contract?"
- ✅ "I need a second opinion on whether to approve this budget request"

#### Examples That Do NOT Trigger
- ❌ "What's the weather like?" (casual chat)
- ❌ "Tell me about machine learning" (informational)
- ❌ "How do I write a for loop in Python?" (instructional - excluded by pattern)
- ❌ "Help me write a blog post" (drafting task)
- ❌ "What are the latest market trends?" (factual query - no decision)

**Exclusion Patterns:**
```python
# Instructional patterns are excluded (not decisional)
instructional_patterns = [
    r'\bhow\s+(do|can)\s+(i|we)\b',  # "how do I", "how can I"
]
```

**Integration Point:**
- `/ui/api/multi-agent` endpoint (quillo_agent/routers/ui_proxy.py:642-650)

**Behavior:**
1. Check prompt with `detect_consequence(text)` before calling multi-agent
2. If True, log: `"[{trace_id}] STRESS TEST v1 activated - consequence detected"`
3. Pass `stress_test_mode=True` to `run_multi_agent_chat()`
4. If False, log: `"[{trace_id}] Normal multi-agent mode - no consequence detected"`

### 2. Lens Assignments

**Location:** `quillo_agent/trust_contract.py:STRESS_TEST_LENSES`

Each peer model receives a specialized analytical lens when Stress Test mode is active:

#### Claude: Risk Lens
**Name:** Risk Lens
**Focus:** Failure modes, downside scenarios, legal/commercial risk

**Instruction:**
```
You are analyzing this decision through the RISK LENS.

Focus on:
- What could go wrong (failure modes)
- Downside scenarios and worst-case outcomes
- Legal, commercial, and compliance risks
- Hidden costs and unintended consequences
- What is irreversible or hard to undo

Be specific about risks, not just cautious.
```

**Why Claude:** Strong reasoning for edge cases and systematic risk analysis

#### DeepSeek: Relationship Lens
**Name:** Relationship Lens
**Focus:** How this lands emotionally, politically, interpersonally

**Instruction:**
```
You are analyzing this decision through the RELATIONSHIP LENS.

Focus on:
- How stakeholders will feel and react
- Political dynamics and power structures
- Trust, credibility, and reputation impact
- Emotional fallout and morale effects
- Who gains/loses influence or standing

Consider both immediate reactions and long-term relationship effects.
```

**Why DeepSeek:** Strong at nuanced social reasoning and stakeholder analysis

#### Gemini: Strategy Lens
**Name:** Strategy Lens
**Focus:** Leverage, timing, alternatives, positioning

**Instruction:**
```
You are analyzing this decision through the STRATEGY LENS.

Focus on:
- Strategic positioning and competitive advantage
- Timing considerations (why now vs. later)
- Opportunity cost and alternatives
- How this moves you toward or away from goals
- Leverage points and force multipliers

Think about the game being played, not just the immediate move.
```

**Why Gemini:** Strong at strategic thinking and opportunity analysis

#### Synthesis: Execution Lens
**Name:** Execution Lens
**Focus:** Clarity, reversibility, next concrete steps

**Location:** `quillo_agent/trust_contract.py:SYNTHESIS_EXECUTION_LENS`

**Instruction:**
```
You are synthesizing the analysis through the EXECUTION LENS.

Focus on:
- Clarity: What exactly is being decided?
- Reversibility: Can this be undone? At what cost?
- Next steps: What concrete actions would follow?
- Decision quality: Do we have enough information?
- Execution risks: What could go wrong in implementation?

Provide actionable synthesis, not just summary.
```

**Why Synthesis:** Converts multi-lens analysis into concrete next steps

### 3. Lens Injection

**Location:** `quillo_agent/services/multi_agent_chat.py:_get_agent_prompt()`

**Integration Logic:**
```python
def _get_agent_prompt(agent_name: str, mode: str = "raw", stress_test_mode: bool = False) -> str:
    from ..trust_contract import get_lens_for_agent, SYNTHESIS_EXECUTION_LENS

    # STRESS TEST v1: Check if lens assignment needed
    lens = None
    if stress_test_mode and agent_name in ["claude", "deepseek", "gemini"]:
        lens = get_lens_for_agent(agent_name)
    elif stress_test_mode and agent_name == "primary_synth":
        lens = SYNTHESIS_EXECUTION_LENS

    # Inject lens instruction into system prompt if assigned
    if lens:
        prompt += f"\n\n{lens['instruction']}"
```

**Behavior:**
1. When `stress_test_mode=True`, retrieve lens for each agent
2. Prepend lens instruction to standard agent prompt
3. Agent responds through assigned lens perspective
4. Synthesis receives all perspectives + Execution Lens

### 4. Stress Test Synthesis Format

**Location:** `quillo_agent/trust_contract.py:format_stress_test_synthesis()`

**Required Fields:**
```python
{
    "mode": "stress_test",
    "decision_being_tested": str,  # What decision is being evaluated
    "top_risks": List[str],        # 2-5 critical risks identified
    "disagreements": List[dict],   # Meaningful differences between lenses
    "best_move": str,              # Primary recommendation
    "alternatives": {
        "safer": str,              # More cautious option
        "bolder": str              # More aggressive option
    },
    "execution_tool": str,         # Response/Rewrite/Argue/Clarity
    "evidence": {
        "used": bool,
        "sources": List[dict]      # If evidence was fetched
    }
}
```

**Disagreement Format:**
```python
{
    "agent": "claude",
    "lens": "Risk",
    "point": "High legal liability risk - termination requires documented cause"
}
```

**Example Output Structure:**
```
**Decision Being Tested:** Should I fire the underperforming manager?

**Top Risks:**
1. Legal liability without proper documentation
2. Team morale impact and uncertainty
3. Knowledge loss and transition cost

**Key Disagreements:**
- Risk Lens (Claude): High legal risk - need documented performance issues
- Relationship Lens (DeepSeek): Will damage team trust if not handled transparently

**Best Move:** Document performance issues thoroughly, have direct conversation with manager, extend PIP by 30 days with clear metrics

**Alternatives:**
- Safer: Extend PIP by 60 days with weekly check-ins and coaching support
- Bolder: Terminate immediately with fair severance package and transparent communication to team

**Execution Tool:** Clarity

**Evidence:** 2 facts from 2 sources (employment law, termination best practices)
```

### 5. Execution Tool Validation

**Location:** `quillo_agent/trust_contract.py:is_valid_execution_tool()`

**Valid Tools:**
- `Response`: Direct answer or recommendation
- `Rewrite`: Draft content (email, message, document)
- `Argue`: Persuasive argument or case
- `Clarity`: Clarifying question or framework

**Validation:**
```python
def is_valid_execution_tool(tool: str) -> bool:
    """Validate execution tool is one of the approved options"""
    valid_tools = ["Response", "Rewrite", "Argue", "Clarity"]
    return tool in valid_tools
```

## Trust Contract Integration

Stress Test v1 preserves ALL Trust Contract v1 behaviors:

### Evidence Default-On
- Still triggers for factual/temporal claims
- Evidence is fetched BEFORE consequence detection
- Agents receive evidence context even in Stress Test mode
- Example: `"Should I sue based on latest employment law?"` → Evidence fetched + Stress Test activated

### No Assumptions Enforcement
- Still blocks vague prompts before Stress Test activation
- Example: `"Should I fire him?"` → Questions asked, no Stress Test (missing context)
- Stress Test only activates if prompt has sufficient context

### Structured Outputs
- Agents still use Evidence/Interpretation/Recommendation format
- Lens instruction is ADDED to standard format requirements
- Both structures are enforced simultaneously

### Disagreement Preservation
- Disagreements are extracted and attributed to lenses
- Example: "Risk Lens recommends caution, Strategy Lens suggests immediate action"
- No forced consensus

### Clear Limitations
- Evidence limitations still stated
- Synthesis notes if decision lacks sufficient information for confident recommendation

## Testing Coverage

**File:** `tests/test_stress_test_v1.py`

**Test Categories (22 tests total):**

### 1. Consequence Detection (9 tests)
- `test_should_i_triggers_consequence`
- `test_decision_framing_triggers_consequence`
- `test_risk_framing_triggers_consequence`
- `test_irreversible_actions_trigger_consequence`
- `test_action_verbs_trigger_consequence`
- `test_casual_chat_no_consequence`
- `test_factual_questions_no_consequence`
- `test_drafting_tasks_no_consequence`
- `test_empty_string_no_consequence`

### 2. Lens Assignments (4 tests)
- `test_get_lens_for_claude` → Risk Lens
- `test_get_lens_for_deepseek` → Relationship Lens
- `test_get_lens_for_gemini` → Strategy Lens
- `test_synthesis_execution_lens_exists` → Execution Lens

### 3. Stress Test Synthesis (2 tests)
- `test_format_stress_test_synthesis_structure`
- `test_stress_test_synthesis_no_disagreements`

### 4. Execution Tool Validation (2 tests)
- `test_valid_execution_tools`
- `test_invalid_execution_tools`

### 5. Integration (4 tests)
- `test_multi_agent_stress_test_activated` → Consequence triggers Stress Test
- `test_multi_agent_normal_mode_casual_chat` → Casual chat does NOT trigger
- `test_stress_test_respects_evidence_default_on` → Evidence + Stress Test both work
- `test_stress_test_blocked_by_no_assumptions` → Vague prompts still blocked

**All 22 tests passing.**

## Known Limitations

1. **Heuristic-Based Detection**
   - Consequence detection uses keyword patterns, not semantic understanding
   - May occasionally miss nuanced decision prompts
   - May occasionally trigger on non-decisional prompts
   - Improvement: Use lightweight ML classifier for better accuracy

2. **Lens Assignment is Fixed**
   - Each model always gets the same lens (Claude=Risk, etc.)
   - No dynamic lens assignment based on decision type
   - Improvement: Could vary lenses based on decision domain

3. **No Conversation Memory**
   - Consequence detection doesn't have access to prior conversation turns
   - Decision context may span multiple messages but detector sees only latest
   - Improvement: Integrate with conversation history when available

4. **Synthesis Format Not Guaranteed**
   - Models may not perfectly follow Stress Test synthesis format
   - Parser may need fallback handling
   - Improvement: Use structured generation APIs when available

5. **No Confidence Scoring**
   - No explicit confidence level on whether consequence was correctly detected
   - User doesn't know if Stress Test was activated
   - Improvement: Could add metadata flag visible to frontend

## Extending Stress Test

### Adding New Consequence Triggers

To add new patterns that should trigger Stress Test:

1. Edit `quillo_agent/trust_contract.py:detect_consequence()`
2. Add keywords or regex patterns to detection logic
3. Add test case in `tests/test_stress_test_v1.py`

Example:
```python
# In trust_contract.py
if re.search(r'\b(pivot|reorg|downsize)\b', text_lower):
    return True  # Organizational changes are consequential

# In test_stress_test_v1.py
def test_organizational_changes_trigger_consequence():
    assert detect_consequence("Should we pivot our business model?") is True
    assert detect_consequence("Planning a company reorganization") is True
```

### Adding New Lenses

To add a new lens perspective:

1. Edit `quillo_agent/trust_contract.py:STRESS_TEST_LENSES`
2. Add lens definition with name, focus, and instruction
3. Update `get_lens_for_agent()` to assign it to an agent
4. Add test case

Example:
```python
# In trust_contract.py
STRESS_TEST_LENSES = {
    # ... existing lenses ...
    "gpt4": {
        "name": "Ethics Lens",
        "focus": "Moral considerations, fairness, values alignment",
        "instruction": """You are analyzing through the ETHICS LENS.

Focus on:
- Moral and ethical implications
- Fairness to all stakeholders
- Values and principles at stake
- Precedent being set
- Long-term character and integrity impact"""
    }
}
```

### Modifying Synthesis Format

To change Stress Test synthesis requirements:

1. Edit `quillo_agent/trust_contract.py:format_stress_test_synthesis()`
2. Update structure and required fields
3. Update synthesis agent prompt in `multi_agent_chat.py`
4. Update test assertions

## Rollback Procedure

To rollback Stress Test v1 (preserving Trust Contract v1):

```bash
# View commits
git log --oneline

# Rollback to before Stress Test implementation
git revert <stress-test-commit-sha>

# Or create branch from before Stress Test
git checkout -b no-stress-test <commit-before-stress-test>
```

**Note:** Stress Test and Trust Contract share `trust_contract.py`, so full rollback requires reverting to pre-Trust Contract state or manually removing only Stress Test functions.

## Operational Monitoring

**Key Metrics to Track:**

1. **Stress Test Activation Rate**
   - Log: `[{trace_id}] STRESS TEST v1 activated - consequence detected`
   - Monitor: Percentage of multi-agent requests triggering Stress Test
   - Expected: 10-30% of multi-agent prompts (adjust if too high/low)

2. **False Positive Rate**
   - Manual review: Are non-decisional prompts triggering Stress Test?
   - User feedback: "This wasn't a decision, just asking a question"
   - Improvement: Tune exclusion patterns based on feedback

3. **False Negative Rate**
   - Manual review: Are genuine decisions NOT triggering Stress Test?
   - User feedback: "I was asking for decision help but got general response"
   - Improvement: Add missed patterns to consequence detection

4. **Lens Distribution**
   - Track which lenses are most often activated
   - Expected: Even distribution if all 3 peer models are used
   - Alert: If one lens never appears (suggests model unavailability)

5. **Evidence + Stress Test Overlap**
   - Log: Both evidence fetch AND stress test activation
   - Monitor: Percentage of Stress Tests that also use Evidence
   - Expected: 20-40% (many decisions involve factual claims)

## Example Scenarios

### Scenario 1: High-Stakes Employment Decision
**Prompt:** "Should I fire this employee for poor performance? He's been with the company 3 years, has had 2 written warnings, and missed his last 3 deadlines. Our policy requires 3 warnings before termination."

**Behavior:**
1. ✅ No assumptions check: Sufficient context provided
2. ✅ Evidence check: May trigger if prompt mentions "latest employment law"
3. ✅ Consequence detection: `detect_consequence()` returns True ("Should I fire")
4. ✅ Stress Test activates
5. ✅ Claude analyzes via Risk Lens (legal liability, documentation)
6. ✅ DeepSeek analyzes via Relationship Lens (team impact, morale)
7. ✅ Gemini analyzes via Strategy Lens (timing, alternatives, positioning)
8. ✅ Synthesis applies Execution Lens (clarity, reversibility, next steps)

**Output:** Structured Stress Test synthesis with risks, disagreements, best move, alternatives

### Scenario 2: Casual Question (No Stress Test)
**Prompt:** "What are the latest trends in machine learning?"

**Behavior:**
1. ✅ No assumptions check: Passes (clear informational query)
2. ✅ Evidence check: Triggers ("latest trends")
3. ❌ Consequence detection: `detect_consequence()` returns False (no decision)
4. ❌ Normal multi-agent mode (no lens assignment)
5. ✅ Evidence fetched and provided
6. ✅ Agents respond with standard format

**Output:** Standard multi-agent response with evidence

### Scenario 3: Vague Decision (Blocked by No Assumptions)
**Prompt:** "Should I fire him?"

**Behavior:**
1. ❌ No assumptions check: FAILS (missing context - who? why? situation?)
2. ❌ Questions returned: "I need details before I can help"
3. ❌ LLM never called
4. ❌ Stress Test never evaluated

**Output:** Clarifying questions asking for context

### Scenario 4: Evidence + Stress Test Combined
**Prompt:** "Should I sue my former employer based on the latest employment law changes in 2026? I was terminated without cause after 5 years."

**Behavior:**
1. ✅ No assumptions check: Sufficient context provided
2. ✅ Evidence check: Triggers ("latest employment law changes in 2026")
3. ✅ Evidence fetched (employment law updates)
4. ✅ Consequence detection: `detect_consequence()` returns True ("Should I sue")
5. ✅ Stress Test activates
6. ✅ All lenses applied with evidence context
7. ✅ Synthesis includes evidence note

**Output:** Stress Test synthesis with evidence-backed risk/relationship/strategy analysis

## References

- [UORIN TRUST CONTRACT v1](./TRUST_CONTRACT_V1.md) - Foundation layer
- [Evidence Layer v1](./EVIDENCE_LAYER_V1.md) - Evidence fetch implementation
- [Multi-Agent Chat Architecture](../MULTI_AGENT_CHAT.md) - Base orchestration

## Changelog

### v1.0 (2026-01-11)
- Initial implementation of STRESS TEST v1
- Automatic consequence detection with heuristic patterns
- Lens assignment system (Risk, Relationship, Strategy, Execution)
- Integration with multi-agent chat service
- Preservation of free-form chat when consequence NOT detected
- Full compatibility with Trust Contract v1
- Comprehensive test coverage (22 tests)
- Documentation and operational guidelines
