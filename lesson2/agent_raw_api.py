"""
ReAct AGENT: Reasoning + Acting Pattern Implementation

This file demonstrates building an agent using the RAW Anthropic API
with the ReAct (Reasoning + Acting) pattern. ReAct interleaves:

    Thought → Action → Observation → Thought → ...

Key ReAct Benefits:
1. Explicit reasoning traces before each action
2. Better interpretability - see WHY the agent acts
3. Improved decision-making through structured thinking
4. Easier debugging - follow the reasoning chain

What this demonstrates:
1. How to prompt for ReAct-style reasoning
2. How to parse Thought/Action/Observation components
3. The agentic loop with explicit reasoning traces
4. Why token counts grow (reasoning adds tokens but improves quality)

Observability:
    This file uses Laminar's automatic instrumentation to trace all
    Anthropic API calls. View traces at https://www.laminar.run

Usage:
    python agent_raw_api.py
"""

import os
import json
import requests
from typing import Any
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Initialize Laminar BEFORE importing anthropic
# This enables automatic instrumentation of all Anthropic API calls
from lmnr import Laminar, Instruments, observe

_laminar_api_key = os.getenv("LAMINAR_API_KEY")
if _laminar_api_key:
    Laminar.initialize(
        project_api_key=_laminar_api_key,
        instruments={Instruments.ANTHROPIC}
    )
    print("  [Laminar] Raw API tracing enabled")
else:
    print("  [Laminar] Not configured - set LAMINAR_API_KEY for tracing")

# Now import anthropic (AFTER Laminar.initialize for auto-instrumentation)
import anthropic

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ENRICHLAYER_API_KEY = os.getenv("ENRICHLAYER_API_KEY")
MODEL = "claude-sonnet-4-20250514"
MAX_TURNS = 5

# ============================================================================
# TOOL DEFINITION (what we send to the API)
# ============================================================================

TOOLS = [
    {
        "name": "fetch_linkedin_profile",
        "description": "Fetch LinkedIn profile data from a URL. Returns profile information including name, title, company, and work history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_url": {
                    "type": "string",
                    "description": "The LinkedIn profile URL to fetch"
                }
            },
            "required": ["profile_url"]
        }
    }
]

SYSTEM_PROMPT = """You are an AI sales assistant specializing in LinkedIn research.

Your goal: Research a prospect and provide a brief summary.

## ReAct Pattern
You MUST follow the ReAct (Reasoning + Acting) pattern. Before EVERY action, explicitly state your reasoning.

Format your responses as:

Thought: [Your reasoning about what you need to do and why]
Action: [Then call the appropriate tool]

After receiving an observation (tool result), continue with another Thought before your next action or final answer.

When you have enough information to answer, format as:

Thought: [Your reasoning about the information gathered]
Final Answer: [Your complete response to the user]

## Available Tools
- fetch_linkedin_profile: Fetches profile data from LinkedIn URLs

## Example
User: Research this LinkedIn profile...

Thought: I need to fetch the LinkedIn profile data first to learn about this person's background and current role.
Action: [call fetch_linkedin_profile tool]

[After receiving observation]

Thought: Now I have the profile data. I can see this person is [name] working as [role] at [company]. I should summarize the key points.
Final Answer: [Summary of the person]

Remember: ALWAYS start with "Thought:" before any action or response.
"""

# ============================================================================
# REACT PARSING HELPERS
# ============================================================================

def parse_react_components(text: str) -> dict:
    """
    Parse ReAct components from LLM output.

    Extracts:
    - Thought: The reasoning trace
    - Final Answer: The concluding response (if present)

    This parsing helps visualize the ReAct pattern in action.
    """
    components = {
        "thoughts": [],
        "final_answer": None,
        "raw_text": text
    }

    lines = text.split('\n')
    current_component = None
    current_content = []

    for line in lines:
        if line.startswith("Thought:"):
            # Save previous component
            if current_component == "thought" and current_content:
                components["thoughts"].append(' '.join(current_content).strip())
            current_component = "thought"
            current_content = [line[8:].strip()]  # After "Thought:"
        elif line.startswith("Final Answer:"):
            # Save previous thought
            if current_component == "thought" and current_content:
                components["thoughts"].append(' '.join(current_content).strip())
            current_component = "final_answer"
            current_content = [line[13:].strip()]  # After "Final Answer:"
        elif current_component:
            # Continue building current component
            current_content.append(line.strip())

    # Save last component
    if current_component == "thought" and current_content:
        components["thoughts"].append(' '.join(current_content).strip())
    elif current_component == "final_answer" and current_content:
        components["final_answer"] = ' '.join(current_content).strip()

    return components


def display_react_trace(text: str, turn: int) -> dict:
    """
    Display ReAct components in a formatted way.

    Returns the parsed components for metrics tracking.
    """
    components = parse_react_components(text)

    # Display thoughts (reasoning traces)
    for i, thought in enumerate(components["thoughts"], 1):
        print(f"\n  💭 THOUGHT {turn}.{i}:")
        # Word wrap for readability
        words = thought.split()
        line = "     "
        for word in words:
            if len(line) + len(word) > 70:
                print(line)
                line = "     " + word
            else:
                line += " " + word if line.strip() else word
        if line.strip():
            print(line)

    # Display final answer if present
    if components["final_answer"]:
        print(f"\n  ✅ FINAL ANSWER:")
        words = components["final_answer"].split()
        line = "     "
        for word in words:
            if len(line) + len(word) > 70:
                print(line)
                line = "     " + word
            else:
                line += " " + word if line.strip() else word
        if line.strip():
            print(line)

    return components


# ============================================================================
# TOOL EXECUTION (we handle this ourselves)
# ============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool and return the result.

    In the SDK, this is handled automatically. Here we do it manually
    so students can see exactly what's happening.

    In ReAct terms, this is the ACTION being executed and the result
    becomes the OBSERVATION.
    """
    print(f"\n  🎯 ACTION: {tool_name}")
    print(f"     Input: {json.dumps(tool_input)}")

    if tool_name == "fetch_linkedin_profile":
        profile_url = tool_input.get("profile_url", "")

        try:
            response = requests.get(
                "https://enrichlayer.com/api/v2/profile",
                params={"profile_url": profile_url},
                headers={"Authorization": f"Bearer {ENRICHLAYER_API_KEY}"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                result = json.dumps(data)
                print(f"\n  👁️ OBSERVATION: Profile fetched successfully")
                print(f"     Name: {data.get('first_name', 'Unknown')} {data.get('last_name', '')}")
                print(f"     Title: {data.get('occupation', 'Unknown')}")
                print(f"     Company: {data.get('company', 'Unknown')}")
                return result
            else:
                error = f"API error {response.status_code}: {response.text[:200]}"
                print(f"\n  👁️ OBSERVATION: ERROR - {error}")
                return error

        except Exception as e:
            error = f"Exception: {str(e)}"
            print(f"\n  👁️ OBSERVATION: ERROR - {error}")
            return error

    return f"Unknown tool: {tool_name}"


# ============================================================================
# THE AGENTIC LOOP (what the SDK does for you)
# ============================================================================

@observe(name="raw_api_research")
def run_agent(user_prompt: str, debug: bool = True) -> dict:
    """
    Run an agentic loop using the raw Anthropic API.

    This shows exactly what happens inside an agent:
    1. Send messages + tools to API
    2. If response has tool_use, execute tool
    3. Add tool result to messages
    4. Repeat until no more tool calls

    Returns metrics about the conversation.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Initialize conversation history
    messages = [
        {"role": "user", "content": user_prompt}
    ]

    # Metrics tracking (including ReAct-specific metrics)
    metrics = {
        "turns": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "tool_calls": [],
        "api_calls": [],
        "thoughts": [],  # Track reasoning traces
        "pattern": "ReAct"
    }

    print(f"\n{'='*70}")
    print("ReAct AGENT - REASONING + ACTING PATTERN")
    print("Thought → Action → Observation → Thought → ...")
    print(f"{'='*70}")

    if debug:
        print(f"\n[INITIAL PROMPT]")
        print(f"  {user_prompt[:200]}...")
        print(f"\n[SYSTEM PROMPT]")
        print(f"  {SYSTEM_PROMPT[:200]}...")
        print(f"\n[TOOLS SENT TO API]")
        print(f"  {len(TOOLS)} tool(s): {[t['name'] for t in TOOLS]}")

    # The agentic loop
    for turn in range(MAX_TURNS):
        metrics["turns"] += 1

        print(f"\n{'─'*70}")
        print(f"TURN {turn + 1}")
        print(f"{'─'*70}")

        if debug:
            # Show what we're sending
            total_message_chars = sum(
                len(json.dumps(m)) for m in messages
            )
            print(f"\n[API REQUEST]")
            print(f"  Messages in history: {len(messages)}")
            print(f"  Approx message size: {total_message_chars:,} chars")
            print(f"  Tools included: Yes ({len(TOOLS)} tools)")

        # Make API call
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Track tokens
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        metrics["total_input_tokens"] += input_tokens
        metrics["total_output_tokens"] += output_tokens

        metrics["api_calls"].append({
            "turn": turn + 1,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "stop_reason": response.stop_reason
        })

        if debug:
            print(f"\n[API RESPONSE]")
            print(f"  Input tokens: {input_tokens:,}")
            print(f"  Output tokens: {output_tokens:,}")
            print(f"  Stop reason: {response.stop_reason}")

        # Process response content
        assistant_content = []
        tool_use_blocks = []
        text_response = ""

        for block in response.content:
            if block.type == "text":
                text_response = block.text
                assistant_content.append({"type": "text", "text": block.text})
                if debug:
                    # Parse and display ReAct components (Thought, Final Answer)
                    react_components = display_react_trace(block.text, turn + 1)
                    # Track thoughts in metrics
                    metrics["thoughts"].extend(react_components.get("thoughts", []))

            elif block.type == "tool_use":
                tool_use_blocks.append(block)
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                metrics["tool_calls"].append({
                    "turn": turn + 1,
                    "tool": block.name,
                    "input": block.input
                })

        # Add assistant message to history
        messages.append({"role": "assistant", "content": assistant_content})

        # If no tool calls, we're done
        if response.stop_reason == "end_turn" or not tool_use_blocks:
            print(f"\n[AGENT COMPLETE]")
            print(f"  Reason: {response.stop_reason}")
            break

        # Execute tools and add results
        tool_results = []
        for tool_block in tool_use_blocks:
            result = execute_tool(tool_block.name, tool_block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result
            })

        # Add tool results to conversation
        messages.append({"role": "user", "content": tool_results})

        if debug:
            print(f"\n[CONVERSATION HISTORY NOW]")
            print(f"  Total messages: {len(messages)}")
            for i, msg in enumerate(messages):
                role = msg["role"]
                content_types = []
                if isinstance(msg["content"], list):
                    content_types = [c.get("type", "text") for c in msg["content"]]
                else:
                    content_types = ["text"]
                print(f"    {i+1}. [{role}] {content_types}")

    # Final summary
    print(f"\n{'='*70}")
    print("ReAct AGENT METRICS SUMMARY")
    print(f"{'='*70}")
    print(f"  Pattern: ReAct (Reasoning + Acting)")
    print(f"  Total turns: {metrics['turns']}")
    print(f"  Reasoning traces (thoughts): {len(metrics['thoughts'])}")
    print(f"  Actions (tool calls): {len(metrics['tool_calls'])}")
    print(f"  Total input tokens: {metrics['total_input_tokens']:,}")
    print(f"  Total output tokens: {metrics['total_output_tokens']:,}")
    print(f"  Total tokens: {metrics['total_input_tokens'] + metrics['total_output_tokens']:,}")

    # Cost estimate (Claude Sonnet pricing)
    input_cost = metrics['total_input_tokens'] * 0.003 / 1000
    output_cost = metrics['total_output_tokens'] * 0.015 / 1000
    total_cost = input_cost + output_cost
    print(f"  Estimated cost: ${total_cost:.6f}")

    print(f"\n[ReAct TRACE SUMMARY]")
    for i, thought in enumerate(metrics["thoughts"], 1):
        preview = thought[:80] + "..." if len(thought) > 80 else thought
        print(f"  Thought {i}: {preview}")

    print(f"\n[TOKEN BREAKDOWN BY TURN]")
    for call in metrics["api_calls"]:
        print(f"  Turn {call['turn']}: {call['input_tokens']:,} in / {call['output_tokens']:,} out")

    metrics["final_response"] = text_response
    metrics["total_cost_usd"] = total_cost

    return metrics


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the raw API agent."""
    linkedin_url = "https://www.linkedin.com/in/jenhsunhuang/"

    prompt = f"""Research this LinkedIn profile and provide a brief summary:

LinkedIn URL: {linkedin_url}

Fetch the profile and tell me about this person."""

    print("\n" + "#"*70)
    print("# ReAct AGENT (RAW ANTHROPIC API)")
    print("# Reasoning + Acting Pattern Implementation")
    print("# See explicit Thought → Action → Observation traces")
    print("#"*70)

    metrics = run_agent(prompt, debug=True)

    print(f"\n{'='*70}")
    print("FINAL RESPONSE")
    print(f"{'='*70}")
    print(metrics.get("final_response", "No response"))

    return metrics


if __name__ == "__main__":
    main()
