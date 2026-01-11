"""
UORIN TRUST CONTRACT v1 - Enforceable Backend Behavior

This module implements the trust-first judgment system behavior:
1. Evidence default-on for factual/temporal prompts
2. No assumptions: ask questions when critical context is missing
3. Structured outputs: Evidence + Interpretation + Recommendation
4. Preserve meaningful disagreement in multi-model synthesis
5. Clear limitations when Evidence unavailable

Pure, testable functions for trust contract enforcement.
"""
from typing import List, Tuple, Dict, Any, Optional
import re
from datetime import datetime


# ============================================================================
# EVIDENCE DEFAULT-ON
# ============================================================================

def classify_prompt_needs_evidence(text: str) -> bool:
    """
    Determine if a prompt contains factual/temporal claims that require Evidence.

    Returns True if the prompt contains indicators that external facts may be needed:
    - Temporal indicators: "latest", "current", "today", "this year", "in 2026", etc.
    - News/market indicators: "news", "market", "price", "stock", "rate", etc.
    - Statistical indicators: "statistics", "data", "numbers", "percentage", etc.
    - Authority indicators: "according to", "study shows", "research", etc.
    - Named entities with factual context: company names + financial terms, etc.

    Args:
        text: User prompt text

    Returns:
        True if Evidence should be fetched, False otherwise
    """
    if not text or not text.strip():
        return False

    text_lower = text.lower()

    # Temporal indicators - strongly suggest need for current information
    temporal_indicators = [
        "latest", "current", "currently", "recent", "recently",
        "today", "this week", "this month", "this year",
        "in 2026", "in 2025", "in 2024",  # Specific years
        "now", "right now", "at the moment",
        "updated", "new", "upcoming"
    ]

    # News and market indicators
    news_market_indicators = [
        "news", "headline", "announcement", "announced",
        "market", "stock", "price", "trading", "ticker",
        "rate", "interest rate", "inflation", "gdp",
        "earnings", "revenue", "profit", "loss",
        "exchange rate", "currency"
    ]

    # Statistical and data indicators
    statistical_indicators = [
        "statistics", "data", "numbers", "figures",
        "percentage", "percent", "%",
        "average", "median", "mean",
        "survey", "poll", "study"
    ]

    # Authority and research indicators
    authority_indicators = [
        "according to", "study shows", "research",
        "report", "analysis", "findings",
        "evidence", "proven", "demonstrated"
    ]

    # Regulatory and compliance
    regulatory_indicators = [
        "law", "regulation", "compliance", "policy",
        "requirement", "mandatory", "legal",
        "tax", "liability"
    ]

    # Check all indicator categories
    all_indicators = (
        temporal_indicators +
        news_market_indicators +
        statistical_indicators +
        authority_indicators +
        regulatory_indicators
    )

    for indicator in all_indicators:
        if indicator in text_lower:
            return True

    # Check for year patterns (e.g., "2026", "2025")
    if re.search(r'\b(20[0-9]{2}|19[0-9]{2})\b', text_lower):
        return True

    # Check for specific question patterns that imply factual queries
    factual_question_patterns = [
        r'\bwhat\s+(is|are|was|were)\s+the\b',
        r'\bhow\s+many\b',
        r'\bhow\s+much\b',
        r'\bwhen\s+(did|does|will)\b',
        r'\bwhere\s+(is|are|was|were)\b',
        r'\bwho\s+(is|are|was|were)\b'
    ]

    for pattern in factual_question_patterns:
        if re.search(pattern, text_lower):
            # But exclude clearly personal questions
            personal_exclusions = ["i", "me", "my", "our", "we"]
            if not any(word in text_lower.split()[:10] for word in personal_exclusions):
                return True

    return False


# ============================================================================
# NO ASSUMPTIONS ENFORCEMENT
# ============================================================================

def enforce_no_assumptions(
    text: str,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Determine if critical information is missing for the user's intent.

    Returns questions to ask the user if essential context is absent.
    The system MUST NOT proceed with LLM calls until these are answered.

    Args:
        text: User prompt text
        context: Optional context dict (conversation history, user prefs, etc.)

    Returns:
        Tuple of (ok_to_proceed: bool, questions: List[str])
        - If ok_to_proceed is False, questions list contains 1-3 precise questions
        - If ok_to_proceed is True, questions list is empty
    """
    if not text or not text.strip():
        return (False, ["What would you like help with?"])

    text_lower = text.lower()
    context = context or {}

    questions = []

    # Pattern 1: Action requests without target specification
    action_patterns = [
        (r'\b(rewrite|draft|edit|revise|improve)\s+(this|the|my)\b', [
            "What specific text should I work with? Please provide the content.",
            "What's the intended audience or purpose?",
            "Are there specific changes or tone adjustments you want?"
        ]),
        (r'\b(email|message|letter)\b', [
            "What's the main purpose of this message?",
            "Who is the recipient?",
            "What key information should it include?"
        ]),
        (r'\b(analyze|review|assess)\s+(this|the|my)\b', [
            "What content should I analyze? Please provide it.",
            "What specific aspects should I focus on?",
            "What's your goal with this analysis?"
        ])
    ]

    for pattern, potential_questions in action_patterns:
        if re.search(pattern, text_lower):
            # Check if actual content is provided in the prompt
            # If prompt is short and action-only, context is missing
            if len(text.split()) < 20:  # Short prompt, likely no content
                if not context.get("has_attachments") and not context.get("has_previous_context"):
                    questions.extend(potential_questions[:2])  # Ask max 2 questions
                    break

    # Pattern 2: Decision requests without criteria
    decision_patterns = [
        r'\bshould i\b',
        r'\bwhat should\b',
        r'\badvice on\b',
        r'\bhelp me decide\b'
    ]

    for pattern in decision_patterns:
        if re.search(pattern, text_lower):
            # Check if essential decision context is missing
            has_context_indicators = any([
                "because" in text_lower,
                "since" in text_lower,
                "given that" in text_lower,
                len(text.split()) > 30,  # Longer prompts likely have context
                context.get("has_previous_context")
            ])

            if not has_context_indicators:
                questions.extend([
                    "What are the main options you're considering?",
                    "What's most important to you in this decision (cost, time, risk, quality)?",
                    "Are there any constraints or deadlines I should know about?"
                ])
                break

    # Pattern 3: Vague or extremely short prompts
    if len(text.split()) < 5 and not context.get("has_previous_context"):
        # Very short prompt without context
        vague_indicators = ["help", "advice", "what", "how", "tell me"]
        if any(word in text_lower for word in vague_indicators):
            questions.append("Could you provide more details about what you need help with?")

    # Return at most 3 questions
    questions = questions[:3]

    # If we have questions, not ok to proceed
    ok_to_proceed = len(questions) == 0

    return (ok_to_proceed, questions)


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_model_output(
    model_name: str,
    evidence_block: Optional[str],
    interpretation: str,
    recommendation: str,
    raw_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a single model's output into standardized structure.

    Required structure:
    - Evidence: Facts from Evidence Block or "No Evidence fetched"
    - Interpretation: Model's analysis, trade-offs, risks
    - Recommendation: Clear next steps with rationale

    Args:
        model_name: Name of the model (e.g., "Claude", "Gemini", "DeepSeek")
        evidence_block: Evidence facts or None
        interpretation: Model's interpretation
        recommendation: Model's recommendation
        raw_response: Optional original unstructured response

    Returns:
        Structured dict with model output
    """
    return {
        "model": model_name,
        "evidence": evidence_block or "No Evidence fetched",
        "interpretation": interpretation,
        "recommendation": recommendation,
        "raw_response": raw_response,
        "structured": bool(interpretation and recommendation),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def format_synthesis(
    decision_framing: str,
    disagreements: List[Dict[str, str]],
    best_move: str,
    alternatives: List[Dict[str, str]],
    suggested_tool: str,
    evidence_sources: Optional[List[Dict[str, str]]] = None,
    evidence_fetched: bool = False
) -> Dict[str, Any]:
    """
    Format Uorin synthesis into standardized structure.

    Required structure:
    - Decision framing (one sentence)
    - Meaningful disagreements (bullets, attributed by model)
    - Best next move (one clear recommendation)
    - 2 Alternatives (safer / bolder)
    - Suggested tool (Response/Rewrite/Argue/Clarity)
    - Evidence used (sources + timestamps) OR "No Evidence fetched"

    Args:
        decision_framing: One-sentence summary of the decision
        disagreements: List of {model, point} dicts showing meaningful differences
        best_move: Primary recommendation
        alternatives: List of 2 alternative approaches with {label, description}
        suggested_tool: Tool name from Response/Rewrite/Argue/Clarity
        evidence_sources: Optional list of evidence sources used
        evidence_fetched: Whether evidence was fetched

    Returns:
        Structured dict with synthesis
    """
    return {
        "decision_framing": decision_framing,
        "disagreements": disagreements,  # [] if consensus
        "best_move": best_move,
        "alternatives": alternatives,  # Should be exactly 2
        "suggested_tool": suggested_tool,
        "evidence": {
            "fetched": evidence_fetched,
            "sources": evidence_sources or [],
            "note": "No Evidence fetched" if not evidence_fetched else None
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def extract_disagreements(model_outputs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract meaningful disagreements from multiple model outputs.

    Compares recommendations and interpretations to find substantive differences.
    Does NOT force consensus - preserves real disagreements.

    Args:
        model_outputs: List of model output dicts (from format_model_output)

    Returns:
        List of disagreement dicts with {model, point}
        Returns empty list if models agree
    """
    if len(model_outputs) < 2:
        return []

    disagreements = []

    # Extract key recommendations
    recommendations = [
        (output["model"], output["recommendation"])
        for output in model_outputs
        if output.get("recommendation")
    ]

    if len(recommendations) < 2:
        return []

    # Simple heuristic: check for contradictory keywords
    cautious_keywords = ["wait", "careful", "risk", "consider", "thorough", "slow"]
    bold_keywords = ["act", "now", "immediately", "decisive", "move", "commit"]

    model_stances = []
    for model, rec in recommendations:
        rec_lower = rec.lower()
        cautious_score = sum(1 for word in cautious_keywords if word in rec_lower)
        bold_score = sum(1 for word in bold_keywords if word in rec_lower)

        if cautious_score > bold_score:
            model_stances.append((model, "cautious", rec))
        elif bold_score > cautious_score:
            model_stances.append((model, "bold", rec))
        else:
            model_stances.append((model, "neutral", rec))

    # Find disagreements
    stances = [stance for _, stance, _ in model_stances]
    if len(set(stances)) > 1:  # More than one unique stance
        for model, stance, rec in model_stances:
            # Extract first sentence of recommendation
            first_sentence = rec.split('.')[0] + '.'
            disagreements.append({
                "model": model,
                "point": first_sentence,
                "stance": stance
            })

    return disagreements


def parse_unstructured_output(raw_text: str, model_name: str) -> Dict[str, Any]:
    """
    Best-effort parsing of unstructured model output into standard format.

    Attempts to extract Evidence/Interpretation/Recommendation sections.
    If parsing fails, wraps entire text as interpretation.

    Args:
        raw_text: Unstructured model response
        model_name: Name of the model

    Returns:
        Structured output dict (may be marked as unstructured)
    """
    # Try to find section markers
    evidence_pattern = r'(?:Evidence|Facts|Sources?):(.*?)(?=\n(?:Interpretation|Analysis|Recommendation)|$)'
    interpretation_pattern = r'(?:Interpretation|Analysis):(.*?)(?=\n(?:Recommendation|Conclusion)|$)'
    recommendation_pattern = r'(?:Recommendation|Conclusion|Suggestion):(.*?)$'

    evidence_match = re.search(evidence_pattern, raw_text, re.DOTALL | re.IGNORECASE)
    interp_match = re.search(interpretation_pattern, raw_text, re.DOTALL | re.IGNORECASE)
    rec_match = re.search(recommendation_pattern, raw_text, re.DOTALL | re.IGNORECASE)

    evidence = evidence_match.group(1).strip() if evidence_match else None
    interpretation = interp_match.group(1).strip() if interp_match else raw_text
    recommendation = rec_match.group(1).strip() if rec_match else "See interpretation above."

    return format_model_output(
        model_name=model_name,
        evidence_block=evidence,
        interpretation=interpretation,
        recommendation=recommendation,
        raw_response=raw_text
    )
