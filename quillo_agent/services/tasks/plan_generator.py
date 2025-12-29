"""
Deterministic task plan generator (v2 Phase 1)

Generates execution plans based on keyword matching.
No LLM calls - uses templates and heuristics.
"""
from typing import List, Dict, Tuple


def generate_plan(intent_text: str) -> Tuple[List[Dict], str]:
    """
    Generate a deterministic plan based on task intent keywords.

    Args:
        intent_text: The task intent text

    Returns:
        Tuple of (plan_steps, summary)
        - plan_steps: List of dicts with step_num, description
        - summary: Brief summary of the plan
    """
    text_lower = intent_text.lower()
    steps = []
    step_num = 1

    # Email/message drafting keywords
    if any(kw in text_lower for kw in ["email", "reply", "respond", "message", "draft"]):
        steps.append({
            "step_num": step_num,
            "description": "Read and analyze the email/message content"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Draft a professional response"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Review and refine the draft for clarity and tone"
        })
        step_num += 1

        summary = "Draft a professional email response"

    # Summarization keywords
    elif any(kw in text_lower for kw in ["summarize", "summary", "extract", "key points", "action items"]):
        steps.append({
            "step_num": step_num,
            "description": "Read and analyze the full content"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Extract key points and main ideas"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Create a concise summary document"
        })
        step_num += 1

        if "action" in text_lower:
            steps.append({
                "step_num": step_num,
                "description": "List action items with owners and deadlines"
            })
            step_num += 1

        summary = "Summarize content and extract key information"

    # Research/analysis keywords
    elif any(kw in text_lower for kw in ["research", "analyze", "investigate", "compare", "review"]):
        steps.append({
            "step_num": step_num,
            "description": "Define research scope and key questions"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Gather and review relevant information"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Analyze findings and identify patterns"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Compile research summary with recommendations"
        })
        step_num += 1

        summary = "Research and analyze the topic systematically"

    # Argument/case building keywords
    elif any(kw in text_lower for kw in ["argue", "argument", "case", "persuade", "convince", "negotiate"]):
        steps.append({
            "step_num": step_num,
            "description": "Identify the core position and goals"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Gather supporting evidence and examples"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Structure the argument logically"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Anticipate and address counterarguments"
        })
        step_num += 1

        summary = "Build a structured, evidence-based case"

    # Default generic plan
    else:
        steps.append({
            "step_num": step_num,
            "description": "Understand the requirements and constraints"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Break down the task into manageable parts"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Execute each part systematically"
        })
        step_num += 1

        steps.append({
            "step_num": step_num,
            "description": "Review and verify the completed work"
        })
        step_num += 1

        summary = "Complete the task step by step"

    return steps, summary
