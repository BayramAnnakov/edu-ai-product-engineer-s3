"""
MCP Tools and Server Configuration

Centralized MCP tools and server setup for reuse across agent workflows.
"""

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from utils import save_report

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.resolve()
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
REPORTS_DIR = BASE_DIR / "reports"


# ============================================================================
# MCP TOOL: Get Top Articles for Period
# ============================================================================


@tool(
    "get_top_articles_for_period",
    "Aggregate homepage snapshots for a publisher and return top articles for the last X hours.",
    {
        "publisher": str,
        "hours": int,
        "max_articles": int,
    },
)
async def get_top_articles_for_period(args: dict[str, Any]) -> dict[str, Any]:
    """
    Aggregate homepage snapshots for a publisher and return top articles.

    Returns data in MCP content format so the agent can properly parse it.
    """
    publisher = args.get("publisher")
    hours = args.get("hours", 24)
    max_articles = args.get("max_articles", 50)

    # Validate input parameters
    if not publisher or not isinstance(publisher, str):
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Error: 'publisher' must be a non-empty string.",
                }
            ]
        }

    if not isinstance(hours, int) or hours <= 0:
        hours = 24
        logger.warning("Invalid hours value, using default: 24")

    if not isinstance(max_articles, int) or max_articles <= 0:
        max_articles = 50
        logger.warning("Invalid max_articles value, using default: 50")

    logger.info(f"Getting top articles for {publisher} over last {hours} hours")

    snapshot_dir = SNAPSHOTS_DIR / publisher
    if not snapshot_dir.exists():
        logger.warning(f"No snapshots found for {publisher}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"No snapshots found for publisher '{publisher}'.",
                }
            ]
        }

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    aggregated = {}  # url -> article_stats

    # 1. Scan and Load Files
    files = sorted(snapshot_dir.glob("*.json"))
    logger.info(f"Found {len(files)} snapshots")

    for path in files:
        try:
            # Parse timestamp from filename
            ts_str = path.stem  # e.g. 2025-12-04T09-00-00Z
            try:
                snapshot_ts = datetime.strptime(ts_str, "%Y-%m-%dT%H-%M-%SZ").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                # Try generic ISO format just in case
                try:
                    snapshot_ts = datetime.fromisoformat(ts_str).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    # Fallback for simple date strings if needed, though filename format should be consistent
                    continue

            if snapshot_ts < since or snapshot_ts > now:
                continue

            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate that loaded data is a list of articles
                if not isinstance(data, list):
                    logger.warning(
                        f"Expected list of articles in {path}, got {type(data).__name__}"
                    )
                    continue
                articles = data

            # 2. Aggregate Logic
            for a in articles:
                url = a.get("link")
                if not url:
                    continue

                if url not in aggregated:
                    aggregated[url] = {
                        "url": url,
                        "title": a.get("title"),
                        "topic_blocks": [],
                        "first_seen_at": snapshot_ts,
                        "last_seen_at": snapshot_ts,
                        "snapshots_count": 0,
                        "times_in_top10": 0,
                        "importance_scores": [],
                        "has_plus_ever": False,
                        "has_update_ever": False,
                        "has_image_ever": False,
                    }

                entry = aggregated[url]
                entry["first_seen_at"] = min(entry["first_seen_at"], snapshot_ts)
                entry["last_seen_at"] = max(entry["last_seen_at"], snapshot_ts)
                entry["snapshots_count"] += 1

                # Safe conversion of importance_score
                score = a.get("importance_score")
                if isinstance(score, (int, float)):
                    entry["importance_scores"].append(float(score))

                if a.get("topic_block"):
                    entry["topic_blocks"].append(a["topic_block"])
                if a.get("position", 999) <= 10:
                    entry["times_in_top10"] += 1
                if a.get("has_plus_badge"):
                    entry["has_plus_ever"] = True
                if a.get("has_update_badge"):
                    entry["has_update_ever"] = True
                if a.get("has_image"):
                    entry["has_image_ever"] = True

        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            continue

    logger.info(f"Aggregated {len(aggregated)} unique URLs")

    # 3. Format Output
    result = []
    for url, entry in aggregated.items():
        scores = entry["importance_scores"]
        avg_score = sum(scores) / len(scores) if scores else 0

        topic_block = None
        if entry["topic_blocks"]:
            topic_block = Counter(entry["topic_blocks"]).most_common(1)[0][0]

        result.append(
            {
                "url": url,
                "title": entry["title"],
                "topic_block": topic_block,
                "first_seen_at": entry["first_seen_at"].isoformat(),
                "last_seen_at": entry["last_seen_at"].isoformat(),
                "snapshots_count": entry["snapshots_count"],
                "times_in_top10": entry["times_in_top10"],
                "max_importance_score": round(max(scores) if scores else 0, 1),
                "avg_importance_score": round(avg_score, 1),
                "has_plus_ever": entry["has_plus_ever"],
                "has_update_ever": entry["has_update_ever"],
                "has_image_ever": entry["has_image_ever"],
            }
        )

    # 4. Sort by importance
    result.sort(
        key=lambda x: (x["max_importance_score"], x["snapshots_count"]), reverse=True
    )

    final_result = result[:max_articles]
    logger.info(f"Returning {len(final_result)} articles (from {len(result)} total)")
    if final_result:
        logger.info(f"First article: {final_result[0].get('title', 'N/A')[:50]}...")

    # Return in MCP content format so agent can properly parse the data
    if not final_result:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "No articles found for the specified period.",
                }
            ]
        }

    # Serialize the list to JSON string for the agent
    result_json = json.dumps(final_result, indent=2, ensure_ascii=False)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Found {len(final_result)} articles:\n\n{result_json}",
            }
        ]
    }


# ============================================================================
# MCP TOOL: Save Report
# ============================================================================


@tool(
    "save_report",
    "Save a report to the reports folder with date-based filename. Use this when you have completed generating a report. ",
    {
        "report_content": str,
        "publisher": str,
        "filename": str,
    },
)
async def save_report_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    MCP tool to save reports. Returns file path in MCP content format.

    Args:
        args: Dictionary with 'report_content' and 'publisher' keys.

    Returns:
        MCP content format with saved file path.
    """
    report_content = args.get("report_content", "")
    publisher = args.get("publisher", "unknown")
    filename = args.get("filename", "report")
    
    if not report_content:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Error: 'report_content' cannot be empty.",
                }
            ],
            "isError": True,
        }

    if not publisher:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Error: 'publisher' must be specified.",
                }
            ],
            "isError": True,
        }

    try:
        # Use the utility function to save the report
        report_path = save_report(report_content, publisher, filename, REPORTS_DIR)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Report saved successfully to: {report_path}",
                }
            ],
            "isError": False,
        }
    except Exception as e:
        logger.error(f"Failed to save report: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error saving report: {str(e)}",
                }
            ],
            "isError": True,
        }


# ============================================================================
# MCP SERVER FACTORY FUNCTIONS
# ============================================================================


def create_homepage_history_server() -> Any:
    """
    Create MCP server with homepage history tools.

    Returns:
        MCP server instance with get_top_articles_for_period tool.
    """
    return create_sdk_mcp_server(
        name="homepage-history",
        version="1.0.0",
        tools=[get_top_articles_for_period],
    )


def create_report_saver_server() -> Any:
    """
    Create MCP server with report saving tools.

    Returns:
        MCP server instance with save_report tool.
    """
    return create_sdk_mcp_server(
        name="report-saver",
        version="1.0.0",
        tools=[save_report_tool],
    )


def create_combined_server() -> Any:
    """
    Create MCP server with both homepage history and report saving tools.

    Returns:
        MCP server instance with all tools.
    """
    return create_sdk_mcp_server(
        name="homepage-tools",
        version="1.0.0",
        tools=[get_top_articles_for_period, save_report_tool],
    )

