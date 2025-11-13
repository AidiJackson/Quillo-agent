"""
Rule-based intent classifier with keyword heuristics
"""
from typing import Dict, Any, List


def classify(text: str) -> Dict[str, Any]:
    """
    Classify intent using deterministic keyword heuristics.

    Returns:
        dict with keys: intent, reasons, slots, confidence
    """
    text_lower = text.lower()
    reasons: List[str] = []
    slots: Dict[str, Any] = {}
    intent = "response"  # default
    confidence = 0.5

    # Intent: response (default for handling, replying, responding)
    response_keywords = ["handle", "respond", "reply", "answer", "client", "email"]
    if any(kw in text_lower for kw in response_keywords):
        intent = "response"
        reasons.append("Detected response keywords (handle/respond/reply/answer/client/email)")
        confidence = 0.7

    # Intent: rewrite
    rewrite_keywords = ["rewrite", "rephrase", "improve", "polish", "refine", "edit"]
    if any(kw in text_lower for kw in rewrite_keywords):
        intent = "rewrite"
        reasons.append("Detected rewrite keywords (rewrite/rephrase/improve/polish)")
        confidence = 0.8

    # Intent: argue
    argue_keywords = ["argue", "debate", "counter", "challenge", "refute", "persuade"]
    if any(kw in text_lower for kw in argue_keywords):
        intent = "argue"
        reasons.append("Detected argumentation keywords (argue/debate/counter/persuade)")
        confidence = 0.8

    # Intent: clarity
    clarity_keywords = ["clarify", "explain", "simplify", "break down", "understand", "eli5"]
    if any(kw in text_lower for kw in clarity_keywords):
        intent = "clarity"
        reasons.append("Detected clarity keywords (clarify/explain/simplify)")
        confidence = 0.8

    # Extract slots: outcome (Defuse, Negotiate, Escalate, etc.)
    if "defuse" in text_lower:
        slots["outcome"] = "Defuse"
        reasons.append("Extracted outcome slot: Defuse")
        confidence = min(confidence + 0.1, 0.9)
    elif "negotiate" in text_lower:
        slots["outcome"] = "Negotiate"
        reasons.append("Extracted outcome slot: Negotiate")
        confidence = min(confidence + 0.1, 0.9)
    elif "escalate" in text_lower:
        slots["outcome"] = "Escalate"
        reasons.append("Extracted outcome slot: Escalate")
        confidence = min(confidence + 0.1, 0.9)

    return {
        "intent": intent,
        "reasons": reasons,
        "slots": slots if slots else None,
        "confidence": confidence
    }
