"""
Reassurance messaging controller for Quillo execution flow.

Provides timed, professional reassurance messages during long-running executions.
Messages are selected from a fixed catalog based on execution context.

Rules:
- Max ONE reassurance message per execution
- Only fires after time threshold
- No narration of internals
- ChatGPT-level confidence tone
"""

import random
from enum import Enum
from typing import Optional


class ReassuranceCategory(str, Enum):
    """Categories of reassurance messages based on execution context."""
    QUALITY_FILTERING = "quality_filtering"
    COMPLEXITY = "complexity"
    STAKES_AWARE = "stakes_aware"


# Fixed message catalog - DO NOT generate dynamically
REASSURANCE_MESSAGES = {
    ReassuranceCategory.QUALITY_FILTERING: [
        "Still working — I've ruled out a few low-quality drafts and I'm refining stronger options.",
        "I'm filtering for quality. Some early drafts didn't meet the clarity threshold.",
        "I'm narrowing this down — prioritising authority and tone alignment.",
    ],
    ReassuranceCategory.COMPLEXITY: [
        "This takes a moment — I'm comparing outcomes across a few approaches.",
        "I'm pressure-testing tone and structure before finalising.",
        "Running a second pass to reduce escalation risk.",
    ],
    ReassuranceCategory.STAKES_AWARE: [
        "This one matters — I'm being deliberate with wording.",
        "Given the context, I'm taking extra care with tone.",
        "I'm refining this to avoid unnecessary friction.",
    ],
}


class ReassuranceController:
    """
    Controls reassurance messaging during execution.

    Timing rules:
    - < 5 seconds: No message
    - 5-12 seconds: Optional (only if internal signal exists)
    - > 12 seconds: Mandatory (exactly one message)
    """

    def __init__(self):
        self.reassurance_sent = False
        self.execution_start_time: Optional[float] = None
        self.category: Optional[ReassuranceCategory] = None

    def start_execution(self, category: ReassuranceCategory = ReassuranceCategory.COMPLEXITY):
        """
        Initialize execution tracking.

        Args:
            category: The reassurance category to use for this execution
        """
        import time
        self.execution_start_time = time.time()
        self.reassurance_sent = False
        self.category = category

    def should_send_reassurance(self, elapsed_seconds: float, has_signal: bool = False) -> bool:
        """
        Determine if reassurance should be sent based on timing rules.

        Args:
            elapsed_seconds: Time elapsed since execution start
            has_signal: Internal signal (e.g., draft rejection, multi-tool use)

        Returns:
            True if reassurance should be sent
        """
        if self.reassurance_sent:
            return False

        # < 5 seconds: Never send
        if elapsed_seconds < 5:
            return False

        # 5-12 seconds: Optional (only if signal exists)
        if 5 <= elapsed_seconds < 12:
            return has_signal

        # > 12 seconds: Mandatory
        return True

    def get_reassurance_message(self) -> Optional[str]:
        """
        Get a reassurance message for the current execution.

        Returns:
            A randomly selected message from the category, or None if already sent
        """
        if self.reassurance_sent or self.category is None:
            return None

        messages = REASSURANCE_MESSAGES.get(self.category, [])
        if not messages:
            return None

        # Mark as sent BEFORE returning to prevent duplicate sends
        self.reassurance_sent = True

        # Select random message from category
        return random.choice(messages)

    def determine_category(
        self,
        stakes: str,
        multi_step: bool = False,
        has_quality_filtering: bool = False
    ) -> ReassuranceCategory:
        """
        Determine appropriate reassurance category based on execution context.

        Args:
            stakes: Judgment stakes level ("low", "medium", "high")
            multi_step: Whether execution involves multiple tools
            has_quality_filtering: Whether quality filtering is active

        Returns:
            The appropriate reassurance category
        """
        # Quality filtering takes precedence
        if has_quality_filtering:
            return ReassuranceCategory.QUALITY_FILTERING

        # Stakes-aware for medium/high stakes
        if stakes in ("medium", "high"):
            return ReassuranceCategory.STAKES_AWARE

        # Complexity for multi-step executions
        if multi_step:
            return ReassuranceCategory.COMPLEXITY

        # Default to complexity
        return ReassuranceCategory.COMPLEXITY

    def reset(self):
        """Reset the controller for a new execution."""
        self.reassurance_sent = False
        self.execution_start_time = None
        self.category = None
