"""Bug Reporter Node - Creates GitHub issues for bug reports.

TODO: Implement this node to:
1. Take a bug report review from state
2. Generate a structured bug report
3. (Optional) Create a GitHub issue via API
4. Return the result in state
"""

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool

from ..audit import utc_timestamp
from ..llm import get_chat_model
from ..parsing import parse_json_dict
from ..state import ReviewState


BUG_REPORTER_PROMPT = """You are a bug report specialist. Your job is to:

1. Analyze the user's bug report
2. Extract key information:
   - Summary (one line)
   - Steps to reproduce (if mentioned)
   - Expected behavior
   - Actual behavior
   - Severity (critical/high/medium/low)
3. Format as a structured bug report

Be concise and technical. Focus on actionable information.
"""


@tool
def create_github_issue(title: str, body: str, labels: list[str]) -> dict:
    """Create a GitHub issue for the bug report.

    USE WHEN: You have a structured bug report ready to submit.

    RETURNS ON SUCCESS: Dict with issue number and URL
    RETURNS ON ERROR: Dict with 'error' key

    Note: This is a simulated tool for the homework.
    In production, you would use the GitHub API.

    Args:
        title: Issue title
        body: Issue body in markdown
        labels: Labels to apply (e.g., ["bug", "high-priority"])

    Returns:
        Issue creation result
    """
    # Simulated response
    import random
    issue_num = random.randint(100, 999)
    return {
        "issue_number": issue_num,
        "url": f"https://github.com/example/repo/issues/{issue_num}",
        "status": "created",
    }


async def bug_reporter_node(state: ReviewState) -> dict:
    """Process a bug report and create a GitHub issue.

    TODO: Implement this function.

    Steps:
    1. Get the bug review from state
    2. Use LLM to generate structured bug report
    3. (Optional) Use the create_github_issue tool
    4. Return state update with the result

    Args:
        state: Current review state

    Returns:
        State update with bug report result
    """
    bug_reviews = state.get("bug_reviews") or []
    current_review = state.get("current_review")

    if not bug_reviews and current_review:
        bug_reviews = [current_review]

    if not bug_reviews:
        return {
            "messages": [AIMessage(content="No bug reviews to process.")]
        }

    llm = get_chat_model("gpt-5-mini", temperature=0)
    bug_results = state.get("bug_results", [])
    messages = []
    processing_errors = []
    audit_log = []

    def normalize_severity(value: str | None) -> str:
        text = (value or "").strip().lower()
        if "crit" in text:
            return "critical"
        if "high" in text:
            return "high"
        if "low" in text:
            return "low"
        if "medium" in text:
            return "medium"
        return "medium"

    def heuristic_severity(review_text: str, rating: int) -> str:
        text = review_text.lower()
        if "crash" in text or "data loss" in text or rating <= 1:
            return "high"
        if "doesn't work" in text or "not working" in text or rating <= 2:
            return "medium"
        return "low"

    for review in bug_reviews:
        prompt = (
            "Return ONLY valid JSON for this bug report with keys: "
            "summary, steps_to_reproduce (array), expected_behavior, "
            "actual_behavior, severity (critical/high/medium/low), confidence (0-1).\n\n"
            f"Review ID: {review['id']}\n"
            f"Rating: {review['rating']}\n"
            f"Text: {review['text']}"
        )

        fallback_report = {
            "summary": review["text"][:80],
            "steps_to_reproduce": [],
            "expected_behavior": "",
            "actual_behavior": review["text"],
            "severity": heuristic_severity(review["text"], review["rating"]),
            "confidence": 0.5,
        }

        try:
            response = await llm.ainvoke([
                SystemMessage(content=BUG_REPORTER_PROMPT),
                HumanMessage(content=prompt),
            ])

            parsed = parse_json_dict(response.content or "")
            if parsed:
                bug_report = parsed
            else:
                bug_report = fallback_report
        except Exception as exc:
            bug_report = fallback_report
            processing_errors.append(
                {
                    "node": "bug_reporter",
                    "review_id": review.get("id"),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            messages.append(
                AIMessage(
                    content=(
                        "LLM unavailable for bug report; used heuristic fallback "
                        f"for review {review.get('id')}. ({type(exc).__name__})"
                    )
                )
            )

        title = bug_report.get("summary") or f"Bug report #{review['id']}"
        steps = bug_report.get("steps_to_reproduce") or []
        steps_text = "\n".join([f"- {step}" for step in steps]) or "- Not provided"
        severity = normalize_severity(str(bug_report.get("severity")))
        bug_report["severity"] = severity
        try:
            bug_report["confidence"] = max(
                0.0, min(float(bug_report.get("confidence", 0.6)), 1.0)
            )
        except (TypeError, ValueError):
            bug_report["confidence"] = 0.6

        body = (
            f"## Summary\n{bug_report.get('summary', '')}\n\n"
            f"## Steps to Reproduce\n{steps_text}\n\n"
            f"## Expected Behavior\n{bug_report.get('expected_behavior', '')}\n\n"
            f"## Actual Behavior\n{bug_report.get('actual_behavior', '')}\n\n"
            f"## Severity\n{severity}\n"
        )

        issue_result = create_github_issue.invoke({
            "title": title,
            "body": body,
            "labels": ["bug", severity],
        })

        action_taken = (
            f"Created GitHub issue #{issue_result.get('issue_number')}"
            if issue_result.get("status") == "created"
            else "Failed to create GitHub issue"
        )

        bug_results.append({
            "id": review["id"],
            "category": "bug",
            "action_taken": action_taken,
            "details": {
                "bug_report": bug_report,
                "issue": issue_result,
            },
        })

        audit_log.append(
            {
                "timestamp": utc_timestamp(),
                "event": "bug_report_created",
                "review_id": review.get("id"),
                "details": {
                    "severity": severity,
                    "issue_number": issue_result.get("issue_number"),
                    "issue_url": issue_result.get("url"),
                },
            }
        )

        messages.append(AIMessage(content=f"Bug processed: {action_taken}"))

    return {
        "bug_results": bug_results,
        "processing_errors": processing_errors,
        "audit_log": audit_log,
        "messages": messages,
    }
