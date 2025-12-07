import asyncio
import argparse
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from mcp_tools import create_combined_server
from utils import display_message

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evening-agent")

# Paths
BASE_DIR = Path(__file__).parent.resolve()
SNAPSHOTS_DIR = BASE_DIR / "snapshots"


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

SYSTEM_PROMPT = """
[ROLE]
You are an Evening Homepage Analysis Agent. Your goal is to analyze homepage history and produce a newsletter recommendation report.

[TOOLS]
1. `homepage-history`:
   - Use `get_top_articles_for_period` FIRST to get the last 24h of data.
   - Use `save_report` to save your final newsletter report when complete.

2. `firecrawl` (PRIMARY content tool):
   - ALWAYS use `scrape_url` as your FIRST CHOICE to inspect article content.
   - It returns clean text/markdown for an article URL.
   - Use this for all candidate articles unless it clearly fails.

3. `playwright` (FALLBACK only):
   - Use browser tools ONLY when Firecrawl is not sufficient:
     - Firecrawl fails or returns an error / empty content,
     - content is clearly behind a paywall and you need to inspect the paywall state,
     - you need a screenshot or to inspect dynamic UI.

[WORKFLOW]
1. Call `get_top_articles_for_period(publisher='<publisher_from_user>', hours=24, max_articles=50)`.
2. Analyze the data: Look for top scoring articles, recurring topics, and "plus" content.
3. Group articles by `topic_block` to identify topic clusters (e.g., Politics, Local, Sports, Culture, etc.).
4. Select articles for the newsletter:
   - For EACH topic cluster, select MULTIPLE articles (at least 2-3 per cluster).
   - Ensure a diverse mix of topics across all clusters.
   - Prioritize articles with high `max_importance_score` and `times_in_top10`.
   - For top articles (especially those with high importance_score), use `scrape_url` or `browser_navigate` + `browser_get_html` to inspect actual content.
   - If you encounter paywalls, try using `browser_navigate` to see if content is accessible.
5. Produce a Markdown Report with:
   - **24h Summary**: What dominated the cycle? Which topics were most prominent?
   - **Top Stories by Topic**: Organize articles by topic clusters. For EACH cluster:
     * List multiple articles (2-4 per cluster)
     * Use the ORIGINAL article titles exactly as provided in the data
     * Include article links (URLs) in markdown format: `[Title](url)`
     * Provide brief content analysis for each article
   - **Local Focus**: 2-3 local interest stories with links.
   - **Recommendations**: Why these specific articles? What makes them newsletter-worthy?

6. Save the Report:
   - After generating the complete report, use the `save_report` tool to save it.
   - Pass the full markdown report content, the publisher name, and filename='evening_report'.
   - The report will be automatically saved with format: YYYY-MM-DD_evening_report_publisher.md
   
[RULES]
- ALWAYS include article links in markdown format: `[Original Title](url)` for every article mentioned.
- Use ORIGINAL article titles exactly as they appear in the data - do not modify or summarize them.
- For each topic cluster, include MULTIPLE articles (minimum 2-3 per cluster).
- Be concise and editorial.
- Explicitly mention if data is missing or if tools returned empty results.
- Do not hallucinate article body content - only use content you actually retrieved via tools.
- Use content scraping tools selectively for top articles to enhance recommendations.
- If scraping fails (paywall, timeout, etc.), mention it in the report but proceed with metadata analysis.
- Structure the report by topic clusters, not just by importance score.
"""


async def run_evening_analysis(publisher: str = "kurier"):
    # Create MCP server with homepage history and report saving tools
    homepage_server = create_combined_server()

    # Get Firecrawl API key from environment
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    
    # Configure Agent
    mcp_servers = {
        "homepage-history": homepage_server,
        "playwright": {"type": "stdio", "command": "npx", "args": ["-y", "@playwright/mcp@latest"]},
    }
    
    # Add Firecrawl MCP server with API key if available
    firecrawl_config: dict[str, Any] = {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
    }
    
    if firecrawl_api_key:
        firecrawl_config["env"] = {"FIRECRAWL_API_KEY": firecrawl_api_key}
        logger.info("Firecrawl API key found, adding to MCP server configuration")
    else:
        logger.warning(
            "FIRECRAWL_API_KEY not found in environment. "
            "Firecrawl MCP server will be added without API key."
        )
    
    mcp_servers["firecrawl"] = firecrawl_config

    options = ClaudeAgentOptions(
        mcp_servers=mcp_servers,
        system_prompt=SYSTEM_PROMPT,
        max_turns=20,
        permission_mode="bypassPermissions",
    )

    print(f"🤖 Starting Evening Agent for {publisher}...")

    try:
        async with ClaudeSDKClient(options=options) as client:
            prompt = f"Analyze the homepage for {publisher} over the last 24 hours and generate the evening newsletter report. Remember to use the save_report tool with filename='evening_report' when you complete the report."

            await client.query(prompt)

            async for msg in client.receive_response():
                display_message(msg)

                if isinstance(msg, ResultMessage):
                    break

    except Exception as e:
        logger.error(f"Agent failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Use argparse to allow specifying the publisher from CLI
    parser = argparse.ArgumentParser(description="Run Evening Homepage Analysis")
    parser.add_argument(
        "--publisher", type=str, default="tagesspiegel", help="Publisher slug (e.g. tagesspiegel)"
    )
    args = parser.parse_args()

    asyncio.run(run_evening_analysis(publisher=args.publisher))

