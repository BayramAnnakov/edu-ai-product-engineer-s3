"""
AGENTIC WORKFLOW: LinkedIn Cold Outreach Generator

This is the "Problem Solver" approach:
- Goal-oriented reasoning
- Self-correction on errors
- Adapts to unexpected inputs
- Slower and more expensive, but robust

Workflow:
1. Agent receives goal: Generate personalized LinkedIn outreach
2. Agent uses tools to achieve goal:
   - fetch_linkedin_profile (custom MCP tool)
   - Reasoning about URL corrections
3. Agent self-corrects on failures
4. Agent generates final message

Expected behavior:
- ✅ Works great on clean, well-formatted URLs
- ✅ Self-corrects typos, missing protocols, variations
- ✅ Handles missing data gracefully
"""

import os
import asyncio
import requests
from typing import Any
from dotenv import load_dotenv

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    tool,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

load_dotenv()

# Initialize API keys
enrichlayer_api_key = os.getenv("ENRICHLAYER_API_KEY")


# ============================================================================
# CUSTOM MCP TOOL: LinkedIn Profile Fetcher
# ============================================================================


@tool(
    "fetch_linkedin_profile",
    "Fetch LinkedIn profile data from EnrichLayer API. Returns profile information or error message.",
    {"profile_url": str},
)
async def fetch_linkedin_profile(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom tool for fetching LinkedIn profiles via EnrichLayer API.

    This runs as an in-process MCP tool - no separate process needed!

    NOTE: Currently simulating failure behavior for testing agent self-correction.
    """
    profile_url = args["profile_url"]

    print(f"  [Tool] Fetching profile: {profile_url}")
    # print(f"  [Tool] ⚠️  SIMULATING API FAILURE (for testing)")

    # Simulate API failure - always return error
    # This mimics a 404 or invalid URL response
    # error_msg = f"API returned 404: Profile not found for URL: {profile_url}"
    # print(f"  [Tool] ❌ Failed: {error_msg}")

    # return {
    #     "content": [{
    #         "type": "text",
    #         "text": f"Error fetching profile: {error_msg}"
    #     }],
    #     "is_error": True
    # }

    # Original implementation (commented out for testing):
    try:
        response = requests.get(
            "https://enrichlayer.com/api/v2/profile",
            params={"profile_url": profile_url},
            headers={"Authorization": f"Bearer {enrichlayer_api_key}"},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            print(
                f"  [Tool] ✅ Success! Found profile for {data.get('first_name', 'Unknown')}"
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully fetched LinkedIn profile:\n{response.text[:500]}",
                    }
                ]
            }
        else:
            error_msg = f"API returned {response.status_code}: {response.text[:200]}"
            print(f"  [Tool] ❌ Failed: {error_msg}")

            return {
                "content": [
                    {"type": "text", "text": f"Error fetching profile: {error_msg}"}
                ],
                "is_error": True,
            }

    except Exception as e:
        error_msg = f"Exception occurred: {str(e)}"
        print(f"  [Tool] ❌ Exception: {error_msg}")

        return {
            "content": [{"type": "text", "text": f"Error: {error_msg}"}],
            "is_error": True,
        }


# ============================================================================
# MESSAGE DISPLAY HELPER
# ============================================================================


def display_message(msg):
    """Display agent messages in a clean, readable format."""
    if isinstance(msg, UserMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"\n👤 User: {block.text}")

    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                # Agent's reasoning/response
                print(f"\n🤖 Agent: {block.text}")
            elif isinstance(block, ToolUseBlock):
                # Agent using a tool
                print(f"\n🔧 Agent using tool: {block.name}")
                if block.input:
                    print(f"   Input: {block.input}")

    elif isinstance(msg, ResultMessage):
        if msg.total_cost_usd:
            print(f"\n💰 Total Cost: ${msg.total_cost_usd:.6f}")


# ============================================================================
# AGENTIC WORKFLOW
# ============================================================================


async def agentic_workflow(linkedin_url: str) -> dict:
    """
    Main agentic workflow function.

    The agent will:
    1. Try to fetch the profile
    2. If it fails, reason about why (malformed URL, typo, etc.)
    3. Self-correct and retry
    4. Generate personalized message
    """
    print(f"\n{'=' * 60}")
    print("AGENTIC WORKFLOW")
    print(f"URL: {linkedin_url}")
    print(f"{'=' * 60}")

    # Create the LinkedIn profile fetcher MCP server
    linkedin_server = create_sdk_mcp_server(
        name="linkedin", version="1.0.0", tools=[fetch_linkedin_profile]
    )

    # Configure the agent
    options = ClaudeAgentOptions(
        # Register our custom MCP server
        mcp_servers={"linkedin": linkedin_server},
        # Allow the agent to use our custom tool
        allowed_tools=["mcp__linkedin__fetch_linkedin_profile"],
        # System prompt: Define the agent's goal and capabilities
        system_prompt="""You are an AI sales assistant specializing in LinkedIn cold outreach.

Your goal: Generate a personalized LinkedIn connection message.

Available tools:
- fetch_linkedin_profile: Fetches profile data from LinkedIn URLs

CRITICAL: URL Self-Correction Strategy
When the fetch_linkedin_profile tool fails, systematically try these fixes in order:

Step 1: Fix Protocol Issues
- If URL lacks "https://", add it
- If URL has "https://" but lacks "www.", add it
- Examples:
  * "linkedin.com/in/user" → "https://www.linkedin.com/in/user"
  * "https://linkedin.com/in/user" → "https://www.linkedin.com/in/user"

Step 2: Fix Common Username Patterns
LinkedIn usernames can have variations. Try:
- Remove hyphens: "john-smith" → "johnsmith"
- Add hyphens between first/last: "johnsmith" → "john-smith"
- Remove trailing slashes
- Examples:
  * "jenhsun-huang" might be "jenhsunhuang"
  * "satya-nadella" might be "satyanadella"

Step 3: Try Known Variations for Famous People
For well-known tech leaders, try common username patterns:
- First name only: "sama" for Sam Altman
- Full name no spaces: "jenhsunhuang" for Jensen Huang
- First initial + last name: "jhuang"

Step 4: If All Attempts Fail
- Extract the person's likely name from the URL pattern
- Use contextual knowledge to identify who they might be
- Generate an appropriate message based on that context
- Be transparent about the limitation

Instructions:
1. Use fetch_linkedin_profile tool with the provided URL
2. If it fails, apply the self-correction strategy above (try at least 2-3 variations)
3. Once you have profile data, extract:
   - First name
   - Current company
   - Role/description
   - Check if company is in tech/software/AI industry
4. Generate personalized outreach message:
   - Start with personal greeting using first name
   - Include specific observation about their company/role
   - Offer clear value proposition with numbers (70% automation)
   - End with soft question about interest
   - **IMPORTANT**: If company is in tech/software/AI → Use rap/verse format
   - Otherwise: Use professional, friendly tone
   - Length: 40-60 words max
   - Signature: Bayram

Context: You're the founder of a B2B SaaS offering AI sales automation that automates 70% of work.
Target: CEOs/Founders/Sales Leaders in $1M+ revenue companies.
""",
        # Limit turns to keep demo fast
        max_turns=10,
    )

    # Create the prompt for the agent
    prompt = f"""Please generate a personalized LinkedIn outreach message for this profile:

LinkedIn URL: {linkedin_url}

Remember to:
1. Try fetching the profile first
2. If it fails, analyze the URL and try to fix it
3. Generate the personalized message based on the profile data"""

    try:
        # Run the agentic workflow
        async with ClaudeSDKClient(options=options) as client:
            # Send the query
            await client.query(prompt)

            # Stream and display the agent's responses
            final_response = None
            async for message in client.receive_response():
                display_message(message)

                # Capture the final text response
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            final_response = block.text

            print(f"\n{'-' * 60}")
            print("GENERATED MESSAGE:")
            print(f"{'-' * 60}")
            print(final_response)
            print(f"{'-' * 60}\n")

            return {"success": True, "message": final_response, "url": linkedin_url}

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}\n")
        return {"success": False, "error": str(e), "url": linkedin_url}


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Run the agentic workflow with test cases."""
    from test_cases import DEMO_PAIR_ALT3

    for label, url in DEMO_PAIR_ALT3:
        print(f"\n{'#' * 60}")
        print(f"# TEST: {label}")
        print(f"{'#' * 60}")
        result = await agentic_workflow(url)

        # Brief pause between tests
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
