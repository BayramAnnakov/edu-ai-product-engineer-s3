"""
Utility functions for agent workflows.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    UserMessage,
)

logger = logging.getLogger(__name__)


def display_message(msg: UserMessage | AssistantMessage | ResultMessage) -> None:
    """
    Display agent messages in a clean, readable format.

    Args:
        msg: Message to display (UserMessage, AssistantMessage, or ResultMessage).
    """
    if isinstance(msg, UserMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"\n👤 User: {block.text}")

    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                # Skip printing very long text blocks (full reports) during streaming
                # They will be printed at the end anyway
                text = block.text
                print(f"\n🤖 Agent: {text}")
            elif isinstance(block, ToolUseBlock):
                print(f"\n🔧 Agent using tool: {block.name}")
                if block.input:
                    print(f"   Input: {block.input}")

    elif isinstance(msg, ResultMessage):
        cost = msg.total_cost_usd or 0.0
        print(f"\n\n💰 Cost: ${cost:.4f}")

        if msg.duration_ms is not None:
            duration_total = msg.duration_ms / 1000
            duration_api = msg.duration_api_ms / 1000 if msg.duration_api_ms else 0.0
            print(f"⏱ Duration: {duration_total:.2f}s (API: {duration_api:.2f}s)")

        if msg.usage:
            input_tokens = msg.usage.get("input_tokens", 0)
            output_tokens = msg.usage.get("output_tokens", 0)
            cache_create = msg.usage.get("cache_creation_input_tokens", 0)
            cache_read = msg.usage.get("cache_read_input_tokens", 0)
            service_tier = msg.usage.get("service_tier", "unknown")

            print(
                f"Tokens — in: {input_tokens}, out: {output_tokens}, "
                f"cache_create: {cache_create}, cache_read: {cache_read}, tier: {service_tier}"
            )

        if msg.session_id:
            print(f"Session ID: {msg.session_id}")

        if msg.num_turns is not None:
            print(f"Agent turns: {msg.num_turns}")

        print("\n✅ Analysis Complete.")


def save_report(report_content: str, publisher: str, filename: str, reports_dir: Path | None = None) -> Path:
    """
    Save the final report to the reports folder with date-based filename.

    Args:
        report_content: The full report content (markdown text).
        publisher: Publisher name for filename.
        reports_dir: Optional path to reports directory. If None, uses default location
                     relative to this file (homework/reports/).

    Returns:
        Path to the saved report file.
    """
    # Default to homework/reports/ if not specified
    if reports_dir is None:
        base_dir = Path(__file__).parent.resolve()
        reports_dir = base_dir / "reports"

    # Ensure reports directory exists
    reports_dir.mkdir(exist_ok=True)

    # Generate filename with date: YYYY-MM-DD_filename_publisher.md
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}_{filename}_{publisher}.md"
    filepath = reports_dir / filename

    # Write report content
    with filepath.open("w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Report saved to: {filepath}")
    return filepath

