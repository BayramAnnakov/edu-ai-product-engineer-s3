"""
RESEARCH AGENT V2: Tool Mastery & Reflection Pattern

This is the main agent for Workshop 2, demonstrating:
1. Improved tool docstrings (tools as user manuals)
2. External feedback via Human-in-the-Loop
3. Structured reflection pattern (V1 -> feedback -> V2)

Evolution from W1:
- W1: Single tool, self-correction via prompt
- W2: Multiple tools, external feedback, structured reflection

The Reflection Pattern:
    Turn 1: Generate V1 research (initial)
    Turn 2: Collect external feedback (human review)
    Turn 3: Reflect and generate V2 (improved)

This breaks the prompt engineering plateau by introducing
real-world signals the LLM couldn't generate by reasoning alone.

Observability:
    Enable Laminar tracing to see what happens "under the hood":
    - Set LAMINAR_API_KEY in .env
    - View traces at https://www.laminar.run
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Suppress noisy Laminar proxy errors (TLS issues that don't affect functionality)
# These errors appear as "hyper::Error" or "Failed to create span" but are non-blocking
class LaminarErrorFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # Filter out known Laminar proxy errors
        if any(x in msg for x in ['hyper::Error', 'BadRecordMac', 'Failed to create span', 'Failed to send trace']):
            return False
        return True

# Apply filter to root logger
logging.getLogger().addFilter(LaminarErrorFilter())

# Import observability utilities (optional - works without Laminar)
from utils.observability import (
    init_observability,
    flush_observations,
    create_tracker,
    observe,
)

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

# Import our custom tools
from tools.linkedin import fetch_linkedin_profile
from tools.human_feedback import request_human_review

# Import our prompts
from prompts.reflection import (
    SYSTEM_PROMPT,
    V1_RESEARCH_PROMPT,
    VALIDATION_PROMPT,
    REFLECTION_PROMPT,
    RESEARCH_CRITERIA,
)

load_dotenv()


# ============================================================================
# STRUCTURED OUTPUTS (OPTIONAL)
# ============================================================================
# Uncomment and use this schema to get validated JSON instead of free-text.
# This is useful when you need to:
# - Save research to a database/CRM
# - Pass results to another agent
# - Ensure consistent output format
#
# Usage: Add to ClaudeAgentOptions or query():
#   options={
#       "output_format": {
#           "type": "json_schema",
#           "schema": RESEARCH_SCHEMA
#       }
#   }

RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "prospect_name": {"type": "string"},
        "company": {"type": "string"},
        "role": {"type": "string"},
        "pain_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "talking_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"]
        }
    },
    "required": ["prospect_name", "pain_points", "talking_points"]
}


# ============================================================================
# MESSAGE DISPLAY HELPER
# ============================================================================

def display_message(msg, tracker=None):
    """
    Display agent messages in a clean, readable format.

    Also logs tool calls to the tracker for Laminar observability.
    """
    if isinstance(msg, UserMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"\n   User: {block.text[:100]}...")

    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                # Agent's reasoning/response
                print(f"\n   Agent: {block.text}")
            elif isinstance(block, ToolUseBlock):
                # Agent using a tool
                print(f"\n   Using tool: {block.name}")
                if block.input:
                    # Show input preview
                    input_str = str(block.input)
                    if len(input_str) > 100:
                        input_str = input_str[:100] + "..."
                    print(f"   Input: {input_str}")

                    # Log tool call to tracker for Laminar
                    if tracker:
                        tool_name = block.name.split("__")[-1]  # Get just the tool name
                        tracker.log_tool_call(tool_name, block.input)

    elif isinstance(msg, ResultMessage):
        if msg.total_cost_usd:
            print(f"\n   Cost: ${msg.total_cost_usd:.6f}")


async def collect_response(client, tracker=None) -> dict:
    """
    Collect and display agent response from streaming.

    Returns dict with:
    - text: The full text response
    - cost_usd: Total cost (if available)
    - input_tokens: Input token count (if available)
    - output_tokens: Output token count (if available)
    """
    response_text = ""
    cost_usd = None
    input_tokens = None
    output_tokens = None

    async for message in client.receive_response():
        display_message(message, tracker)

        # Capture text responses
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text + "\n"

        # Capture cost and token info from ResultMessage
        elif isinstance(message, ResultMessage):
            cost_usd = getattr(message, 'total_cost_usd', None)
            # Try to get token counts (may not be available in all SDK versions)
            input_tokens = getattr(message, 'input_tokens', None)
            output_tokens = getattr(message, 'output_tokens', None)

    return {
        "text": response_text.strip(),
        "cost_usd": cost_usd,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


# ============================================================================
# RESEARCH AGENT V2 - MAIN FUNCTION
# ============================================================================

@observe()  # Laminar decorator - traces all SDK interactions
async def research_with_reflection(linkedin_url: str) -> dict:
    """
    Research Agent V2 - with reflection pattern.

    This implements the core teaching of Workshop 2:
    - External feedback breaks the prompt engineering plateau
    - Structured reflection (V1 -> feedback -> V2) produces better output
    - Human-in-the-loop is essential for production AI systems

    Flow:
        Turn 1: Generate V1 research using fetch_linkedin_profile
        Turn 2: Collect external feedback using request_human_review
        Turn 3: Reflect on feedback and generate improved V2 research

    The @observe() decorator enables Laminar to capture all SDK
    communications within this function for full visibility.

    Args:
        linkedin_url: LinkedIn profile URL to research

    Returns:
        dict with v1_research, feedback, v2_research, and success status
    """
    print(f"\n{'='*60}")
    print(f"RESEARCH AGENT V2 - WITH REFLECTION PATTERN")
    print(f"{'='*60}")
    print(f"URL: {linkedin_url}")
    print(f"{'='*60}")

    # Create observability tracker for this research session
    tracker = create_tracker("research-with-reflection")

    # Setup MCP server with BOTH tools
    # Tool names will be: mcp__research__fetch_linkedin_profile
    #                     mcp__research__request_human_review
    research_server = create_sdk_mcp_server(
        name="research",
        version="2.0.0",
        tools=[fetch_linkedin_profile, request_human_review]
    )

    options = ClaudeAgentOptions(
        mcp_servers={"research": research_server},
        allowed_tools=[
            # Custom MCP tools
            "mcp__research__fetch_linkedin_profile",
            "mcp__research__request_human_review",
            # Standard SDK tools for file operations
            "Read",
            "Write",
            "Edit",
            # Standard SDK tools for task management
            "TodoRead",
            "TodoWrite",
        ],
        system_prompt=SYSTEM_PROMPT,
        max_turns=15,
        # output_format={
        #   "type": "json_schema",
        #   "schema": RESEARCH_SCHEMA
        # }
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            # ========================================
            # TURN 1: Generate V1 Research
            # ========================================
            print(f"\n{'='*60}")
            print("TURN 1: Generating Initial Research (V1)")
            print(f"{'='*60}")
            print("The agent will fetch the LinkedIn profile and generate")
            print("initial research based on the data...")
            print("-" * 40)

            v1_prompt = V1_RESEARCH_PROMPT.format(linkedin_url=linkedin_url)

            # Track this generation in Laminar
            tracker.start_generation("Turn 1: V1 Research", v1_prompt)

            await client.query(v1_prompt)
            v1_result = await collect_response(client, tracker)
            v1_response = v1_result["text"]

            # End generation tracking with response and metrics
            tracker.end_generation(
                output=v1_response,
                input_tokens=v1_result.get("input_tokens"),
                output_tokens=v1_result.get("output_tokens"),
                cost_usd=v1_result.get("cost_usd")
            )

            print(f"\n{'='*60}")
            print("V1 Research Complete")
            print(f"{'='*60}")

            # ========================================
            # TURN 2: Collect External Feedback (HITL)
            # ========================================
            print(f"\n{'='*60}")
            print("TURN 2: Collecting External Feedback (Human-in-the-Loop)")
            print(f"{'='*60}")
            print("The agent will now request human review.")
            print("This is EXTERNAL FEEDBACK - signals the LLM cannot")
            print("generate through reasoning alone.")
            print("-" * 40)

            # Track this generation in Laminar
            tracker.start_generation("Turn 2: External Feedback (HITL)", VALIDATION_PROMPT)

            await client.query(VALIDATION_PROMPT)
            feedback_result = await collect_response(client, tracker)
            feedback_response = feedback_result["text"]

            tracker.end_generation(
                output=feedback_response,
                input_tokens=feedback_result.get("input_tokens"),
                output_tokens=feedback_result.get("output_tokens"),
                cost_usd=feedback_result.get("cost_usd")
            )

            print(f"\n{'='*60}")
            print("External Feedback Collected")
            print(f"{'='*60}")

            # ========================================
            # TURN 3: Reflection -> V2
            # ========================================
            print(f"\n{'='*60}")
            print("TURN 3: Reflection -> Improved Research (V2)")
            print(f"{'='*60}")
            print("The agent will now reflect on the feedback and generate")
            print("an improved version of the research...")
            print("-" * 40)

            reflection_prompt = REFLECTION_PROMPT.format(
                feedback=feedback_response,
                criteria=RESEARCH_CRITERIA
            )

            # Track this generation in Laminar
            tracker.start_generation("Turn 3: Reflection → V2", reflection_prompt)

            await client.query(reflection_prompt)
            v2_result = await collect_response(client, tracker)
            v2_response = v2_result["text"]

            tracker.end_generation(
                output=v2_response,
                input_tokens=v2_result.get("input_tokens"),
                output_tokens=v2_result.get("output_tokens"),
                cost_usd=v2_result.get("cost_usd")
            )

            print(f"\n{'='*60}")
            print("V2 Research Complete")
            print(f"{'='*60}")

            # ========================================
            # End trace and show summary
            # ========================================
            trace_summary = tracker.end_trace()
            if trace_summary:
                print(f"\n{'='*60}")
                print("OBSERVABILITY SUMMARY")
                print(f"{'='*60}")
                print(f"  Generations: {trace_summary['generations']}")
                # Only show token count if available (some SDK versions don't report this)
                if trace_summary.get('input_tokens', 0) > 0 or trace_summary.get('output_tokens', 0) > 0:
                    print(f"  Total tokens: {trace_summary['input_tokens']} in / {trace_summary['output_tokens']} out")
                print(f"  Total cost: ${trace_summary['cost_usd']:.6f}")
                print(f"  Duration: {trace_summary['duration_s']:.2f}s")
                print(f"{'='*60}")

            print(f"\n{'='*60}")
            print("RESEARCH COMPLETE - V1 vs V2 COMPARISON")
            print(f"{'='*60}")

            return {
                "success": True,
                "v1_research": v1_response,
                "feedback": feedback_response,
                "v2_research": v2_response,
                "linkedin_url": linkedin_url
            }

    except Exception as e:
        print(f"\n Error during research: {str(e)}")
        # Still end the trace even on error
        tracker.end_trace()
        return {
            "success": False,
            "error": str(e),
            "linkedin_url": linkedin_url
        }


# ============================================================================
# COMPARISON HELPER
# ============================================================================

def show_comparison(result: dict):
    """Show side-by-side comparison of V1 vs V2 research."""
    if not result.get("success"):
        print(f"\nResearch failed: {result.get('error')}")
        return

    print(f"\n{'='*60}")
    print("V1 vs V2 COMPARISON")
    print(f"{'='*60}")

    # Show V1 summary (first 1500 chars to capture key sections)
    print("\n--- V1 (Before External Feedback) ---")
    v1 = result.get("v1_research", "")
    print(v1[:1500] + "\n..." if len(v1) > 1500 else v1)

    # Show feedback received (this is the key external signal)
    print("\n--- External Feedback Received ---")
    feedback = result.get("feedback", "")
    print(feedback[:800] + "\n..." if len(feedback) > 800 else feedback)

    # Show V2 summary (first 1500 chars to capture improvements)
    print("\n--- V2 (After Reflection) ---")
    v2 = result.get("v2_research", "")
    print(v2[:1500] + "\n..." if len(v2) > 1500 else v2)

    print(f"\n{'='*60}")
    print("KEY INSIGHT: The V2 research incorporates external feedback")
    print("that the LLM couldn't generate through reasoning alone.")
    print(f"{'='*60}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Run the research agent with test prospects."""
    from demo_data import DEMO_PROSPECT

    # Initialize observability (optional - works without Laminar)
    observability_enabled = init_observability()

    # Get the test URL
    label, url = DEMO_PROSPECT

    print(f"\n{'#'*60}")
    print(f"# WORKSHOP 2: Tool Mastery & Reflection Pattern")
    print(f"# Test: {label}")
    print(f"{'#'*60}")

    # Run research with reflection
    result = await research_with_reflection(url)

    # Show comparison
    show_comparison(result)

    # Flush observability traces before exit
    if observability_enabled:
        flush_observations()
        print(f"\n{'='*60}")
        print("View trace at: https://www.laminar.run")
        print(f"{'='*60}")

    return result


if __name__ == "__main__":
    asyncio.run(main())
