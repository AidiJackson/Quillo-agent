"""
Plan execution service with LLM-based tool simulation
"""
import uuid
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
from ..schemas import PlanStep, ExecutionArtifact
from .llm import LLMRouter
from ..config import settings


# Offline templates for tool execution when no LLM is available
OFFLINE_TOOL_TEMPLATES = {
    "response_generator": """[SIMULATED RESPONSE]

Based on your request, here's a professional response draft:

Dear [Recipient],

Thank you for your message. I appreciate you taking the time to reach out regarding this matter.

After careful consideration, I wanted to address your concerns directly and provide clarity on the situation.

I look forward to your response and working together to find a mutually beneficial solution.

Best regards,
[Your Name]

(Note: This is a simulated response. In production, this would be generated based on your specific context and preferences.)""",

    "rewriter": """[SIMULATED REWRITE]

Original text has been professionally rewritten with improved clarity and tone:

---

The content has been restructured to enhance readability and maintain a professional tone while preserving the original intent. Key improvements include:

• Clearer structure and organization
• More concise phrasing
• Professional language choices
• Better flow and coherence

(Note: This is a simulated rewrite. In production, this would show the actual rewritten content.)""",

    "argument_builder": """[SIMULATED ARGUMENT]

Here's a structured argument for your position:

**Main Thesis:**
The proposed approach offers significant advantages and should be adopted.

**Key Supporting Points:**

1. **Evidence-Based Reasoning**: Data supports this direction
2. **Practical Benefits**: Clear advantages in implementation
3. **Risk Mitigation**: Addresses potential concerns proactively

**Conclusion:**
The evidence strongly suggests this is the optimal path forward.

(Note: This is a simulated argument. In production, this would be customized to your specific situation.)""",

    "clarity_simplifier": """[SIMULATED CLARIFICATION]

Here's a clearer explanation of the complex concept:

**In Simple Terms:**
The main idea is straightforward when broken down into digestible parts.

**Step-by-Step Breakdown:**
1. First, understand the basic premise
2. Then, see how it applies practically
3. Finally, recognize the broader implications

**Key Takeaway:**
By simplifying the language and using concrete examples, the concept becomes much more accessible.

(Note: This is a simulated clarification. In production, this would address your specific content.)""",

    "tone_adjuster": """[SIMULATED TONE ADJUSTMENT]

The tone has been adjusted to better match the situation and audience:

The message now reflects a more appropriate level of formality and emotional resonance while maintaining professionalism.

(Note: This is a simulated adjustment. In production, this would show the actual tone-adjusted content.)""",

    "conflict_resolver": """[SIMULATED CONFLICT RESOLUTION]

De-escalation Strategy Applied:

• Acknowledge the other party's perspective
• Find common ground
• Propose collaborative solutions
• Maintain respectful, neutral language
• Focus on future resolution rather than past blame

(Note: This is a simulated resolution strategy. In production, this would be tailored to your specific conflict.)""",

    "style_enhancer": """[SIMULATED STYLE ENHANCEMENT]

Premium stylistic improvements applied:

The writing now features enhanced rhetorical devices, varied sentence structure, and more sophisticated vocabulary choices while remaining accessible.

(Note: This is a simulated enhancement. In production, this would show the actual enhanced content.)""",

    "counter_analyzer": """[SIMULATED COUNTER-ANALYSIS]

Potential Counter-Arguments Addressed:

1. **Objection A**: Anticipated concern about X
   - **Response**: Evidence and reasoning to address this

2. **Objection B**: Possible pushback on Y
   - **Response**: How this is mitigated

(Note: This is a simulated analysis. In production, this would identify actual counter-arguments to your specific position.)""",

    "example_generator": """[SIMULATED EXAMPLES]

Concrete Examples to Illustrate:

**Example 1**: Practical scenario showing the concept in action
**Example 2**: Real-world application demonstrating the principle
**Example 3**: Relatable analogy making the idea more tangible

(Note: This is a simulated example set. In production, these would be specific to your content.)""",

    "general_assistant": """[SIMULATED ASSISTANCE]

Here's help with your request:

Your input has been processed and a suitable response has been generated based on the context provided.

(Note: This is a generic simulated response. In production, this would be customized to your specific needs.)""",
}


class ExecutionService:
    """Service for executing plan steps with LLM-based tool simulation"""

    def __init__(self):
        self.llm_router = LLMRouter()

    async def execute_plan(
        self,
        text: str,
        intent: str,
        slots: Optional[Dict[str, Any]],
        plan_steps: List[PlanStep],
        user_id: Optional[str] = None,
        dry_run: bool = True
    ) -> Tuple[str, List[ExecutionArtifact], str, List[str]]:
        """
        Execute a plan by simulating each tool with LLM calls.

        Args:
            text: Original user input
            intent: Detected intent
            slots: Extracted slots
            plan_steps: List of plan steps to execute
            user_id: Optional user identifier
            dry_run: If true, adds safety warnings

        Returns:
            Tuple of (output_text, artifacts, provider_used, warnings)
        """
        trace_id = str(uuid.uuid4())
        logger.info(f"Executing plan with {len(plan_steps)} steps (trace_id={trace_id})")

        artifacts: List[ExecutionArtifact] = []
        warnings: List[str] = []
        provider_used = "offline"
        accumulated_output = ""

        # Add dry run warning
        if dry_run:
            warnings.append("DRY RUN MODE: No actual external actions performed")

        # Determine provider availability
        if settings.openrouter_api_key:
            provider_used = "openrouter"
        elif settings.anthropic_api_key:
            provider_used = "anthropic"

        # Execute each step
        for idx, step in enumerate(plan_steps):
            logger.debug(f"Executing step {idx}: {step.tool}")

            # Normalize tool name
            tool_name = self._normalize_tool_name(step.tool)

            # Generate input for this step
            input_summary = self._create_input_summary(text, intent, slots, step, idx)

            # Execute the tool (LLM simulation)
            try:
                output = await self._execute_tool(
                    tool_name=tool_name,
                    intent=intent,
                    slots=slots,
                    text=text,
                    rationale=step.rationale,
                    provider=provider_used,
                    previous_output=accumulated_output if accumulated_output else None
                )

                accumulated_output = output

                # Create artifact
                artifact = ExecutionArtifact(
                    step_index=idx,
                    tool=step.tool,
                    input_excerpt=input_summary[:200],  # Truncate for brevity
                    output_excerpt=output[:200] if output else "(no output)"
                )
                artifacts.append(artifact)

            except Exception as e:
                logger.error(f"Step {idx} execution failed: {e}")
                error_output = f"[ERROR] Step {idx} ({step.tool}) failed: {str(e)}"
                artifact = ExecutionArtifact(
                    step_index=idx,
                    tool=step.tool,
                    input_excerpt=input_summary[:200],
                    output_excerpt=error_output[:200]
                )
                artifacts.append(artifact)
                warnings.append(f"Step {idx} ({step.tool}) encountered an error")

        # Final output is the last accumulated output
        final_output = accumulated_output if accumulated_output else "[No output generated]"

        logger.info(f"Plan execution completed (trace_id={trace_id}, provider={provider_used})")

        return final_output, artifacts, provider_used, warnings

    def _normalize_tool_name(self, tool_name: str) -> str:
        """Normalize tool names to standard format"""
        # Convert tool names to lowercase and remove underscores
        normalized = tool_name.lower().replace("_", "")

        # Map common variations
        tool_map = {
            "responsegenerator": "response_generator",
            "response": "response_generator",
            "rewriter": "rewriter",
            "rewrite": "rewriter",
            "argumentbuilder": "argument_builder",
            "argue": "argument_builder",
            "argument": "argument_builder",
            "claritysimplifier": "clarity_simplifier",
            "clarity": "clarity_simplifier",
            "toneadjuster": "tone_adjuster",
            "conflictresolver": "conflict_resolver",
            "styleenhancer": "style_enhancer",
            "counteranalyzer": "counter_analyzer",
            "examplegenerator": "example_generator",
            "generalassistant": "general_assistant",
        }

        return tool_map.get(normalized, tool_name)

    def _create_input_summary(
        self,
        text: str,
        intent: str,
        slots: Optional[Dict[str, Any]],
        step: PlanStep,
        step_index: int
    ) -> str:
        """Create a summary of inputs for a step"""
        summary_parts = [
            f"Step {step_index}: {step.tool}",
            f"Intent: {intent}",
        ]

        if slots:
            summary_parts.append(f"Slots: {slots}")

        summary_parts.append(f"Original text: {text[:100]}...")

        return " | ".join(summary_parts)

    async def _execute_tool(
        self,
        tool_name: str,
        intent: str,
        slots: Optional[Dict[str, Any]],
        text: str,
        rationale: str,
        provider: str,
        previous_output: Optional[str] = None
    ) -> str:
        """
        Execute a single tool by calling LLM or using offline template.

        Args:
            tool_name: Normalized tool name
            intent: User intent
            slots: Extracted slots
            text: Original user text
            rationale: Why this step is needed
            provider: openrouter/anthropic/offline
            previous_output: Output from previous step (for chaining)

        Returns:
            Tool execution output
        """
        # Construct tool-specific prompt
        tool_prompt = self._build_tool_prompt(
            tool_name=tool_name,
            intent=intent,
            slots=slots,
            text=text,
            rationale=rationale,
            previous_output=previous_output
        )

        # Try LLM execution
        if provider == "openrouter":
            try:
                result = await self.llm_router.answer_business_question(
                    text=tool_prompt,
                    profile_excerpt=""
                )
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenRouter tool execution failed: {e}, falling back to offline")

        elif provider == "anthropic":
            try:
                # Use Anthropic API for tool execution
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": settings.anthropic_api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 1000,
                            "messages": [{"role": "user", "content": tool_prompt}]
                        },
                        timeout=30.0
                    )
                    response.raise_for_status()
                    content = response.json()["content"][0]["text"]
                    return content
            except Exception as e:
                logger.warning(f"Anthropic tool execution failed: {e}, falling back to offline")

        # Offline fallback
        return OFFLINE_TOOL_TEMPLATES.get(tool_name, OFFLINE_TOOL_TEMPLATES["general_assistant"])

    def _build_tool_prompt(
        self,
        tool_name: str,
        intent: str,
        slots: Optional[Dict[str, Any]],
        text: str,
        rationale: str,
        previous_output: Optional[str]
    ) -> str:
        """Build a tool-specific prompt for LLM execution"""
        prompt_parts = []

        # Tool-specific instructions
        tool_instructions = {
            "response_generator": "Generate a professional response draft based on the following context:",
            "rewriter": "Rewrite the following text to be more professional and clear:",
            "argument_builder": "Build a structured argument for the following position:",
            "clarity_simplifier": "Simplify and clarify the following complex concept:",
            "tone_adjuster": "Adjust the tone of the following to be more appropriate:",
            "conflict_resolver": "Provide conflict resolution strategies for:",
            "style_enhancer": "Enhance the writing style of the following:",
            "counter_analyzer": "Identify and address potential counter-arguments for:",
            "example_generator": "Generate concrete examples to illustrate:",
            "general_assistant": "Provide assistance with the following:",
        }

        instruction = tool_instructions.get(tool_name, "Process the following:")
        prompt_parts.append(instruction)
        prompt_parts.append(f"\nUser request: {text}")
        prompt_parts.append(f"\nIntent: {intent}")

        if slots:
            prompt_parts.append(f"\nContext slots: {slots}")

        prompt_parts.append(f"\nRationale: {rationale}")

        if previous_output:
            prompt_parts.append(f"\nPrevious step output: {previous_output[:500]}...")

        prompt_parts.append("\nProvide your output:")

        return "\n".join(prompt_parts)


# Create singleton instance
execution_service = ExecutionService()
