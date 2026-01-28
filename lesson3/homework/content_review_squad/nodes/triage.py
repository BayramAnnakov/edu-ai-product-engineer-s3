"""Triage Node - Classifies reviews and routes to appropriate handler.

TODO: Implement this node to:
1. Take a review from state
2. Use an LLM to classify it as: bug, feature, or praise
3. Return the classification in state

This node should use conditional edges to route to different branches.
"""

from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..audit import utc_timestamp
from ..llm import get_chat_model
from ..parsing import parse_json_dict
from ..state import ReviewState


TRIAGE_SYSTEM_PROMPT = """You are a review triage specialist. Your job is to classify
product reviews into one of three categories:

1. BUG - The review describes a bug, error, crash, or something not working correctly
2. FEATURE - The review requests a new feature or improvement
3. PRAISE - The review is positive feedback, testimonial, or general appreciation

Analyze the review text and rating.

Return ONLY valid JSON with keys:
- category: BUG | FEATURE | PRAISE
- confidence: float 0 to 1
- rationale: short explanation
- language: ISO 639-1 code (e.g., en, ru)
"""


TRIAGE_CONFIDENCE_THRESHOLD = 0.65


async def triage_node(state: ReviewState) -> dict:
    """Classify the current review and prepare for routing.

    TODO: Implement this function.

    Steps:
    1. Get the current review from state
    2. Use an LLM to classify it (use gpt-5-mini for cost efficiency)
    3. Parse the classification
    4. Return state update with the classification

    The graph's conditional edges will use this classification to route
    to the appropriate handler (bug_reporter, feature_analyst, or praise_logger).

    Args:
        state: Current review state

    Returns:
        State update with classification result
    """
    reviews = state.get("reviews") or []
    current_review = state.get("current_review")

    if not reviews and current_review:
        reviews = [current_review]

    if not reviews:
        return {
            "messages": [AIMessage(content="No reviews to classify.")]
        }

    llm = get_chat_model("gpt-5-mini", temperature=0)

    triage_results = []
    bug_reviews = []
    feature_reviews = []
    praise_reviews = []
    state_messages = []
    processing_errors = []
    triage_needs_review = state.get("triage_needs_review", [])
    review_queue = []
    audit_log = []

    def guess_language(text: str) -> str:
        for char in text:
            if "\u0400" <= char <= "\u04FF":
                return "ru"
        if any(char.isalpha() for char in text):
            return "en"
        return "unknown"

    def normalize_category(raw_value: str) -> Literal["bug", "feature", "praise"]:
        value = (raw_value or "").upper()
        if "BUG" in value:
            return "bug"
        if "FEATURE" in value:
            return "feature"
        return "praise"

    def clamp_confidence(value: float | None, fallback: float) -> float:
        if value is None:
            return fallback
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return fallback

    def heuristic_category(review: dict) -> Literal["bug", "feature", "praise"]:
        text = (review.get("text") or "").lower()
        rating = int(review.get("rating") or 0)

        bug_keywords = [
            "crash",
            "bug",
            "error",
            "issue",
            "doesn't work",
            "not working",
            "fail",
            "broken",
            "freeze",
        ]
        feature_keywords = [
            "feature",
            "would love",
            "wish",
            "please add",
            "could you",
            "request",
            "improvement",
            "enhancement",
            "dark mode",
        ]

        if rating <= 2 or any(keyword in text for keyword in bug_keywords):
            return "bug"
        if any(keyword in text for keyword in feature_keywords):
            return "feature"
        if rating >= 4:
            return "praise"
        return "feature"

    for review in reviews:
        prompt_messages = [
            SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Classify this review:\n"
                    f"Review ID: {review['id']}\n"
                    f"Rating: {review['rating']}\n"
                    f"Text: {review['text']}"
                )
            ),
        ]

        try:
            response = await llm.ainvoke(prompt_messages)
            parsed = parse_json_dict(response.content or "")

            if parsed:
                category = normalize_category(str(parsed.get("category", "")))
                confidence = clamp_confidence(parsed.get("confidence"), 0.6)
                rationale = str(parsed.get("rationale", "")).strip()
                language = str(parsed.get("language", "")) or guess_language(review["text"])
            else:
                raw_category = (response.content or "").strip().upper()
                category = normalize_category(raw_category)
                confidence = 0.55
                rationale = ""
                language = guess_language(review["text"])
        except Exception as exc:
            category = heuristic_category(review)
            confidence = 0.45
            rationale = "heuristic fallback"
            language = guess_language(review["text"])
            processing_errors.append(
                {
                    "node": "triage",
                    "review_id": review.get("id"),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            state_messages.append(
                AIMessage(
                    content=(
                        "LLM unavailable for triage; used heuristic classification "
                        f"for review {review.get('id')}. ({type(exc).__name__})"
                    )
                )
            )

        if category == "bug":
            bug_reviews.append(review)
        elif category == "feature":
            feature_reviews.append(review)
        else:
            praise_reviews.append(review)

        low_confidence = confidence < TRIAGE_CONFIDENCE_THRESHOLD
        triage_result = {
            "id": review["id"],
            "category": category,
            "confidence": confidence,
            "language": language,
            "rationale": rationale,
            "low_confidence": low_confidence,
        }

        triage_results.append(triage_result)
        if low_confidence:
            triage_needs_review.append(triage_result)
            review_queue.append(
                {
                    "type": "triage",
                    "review_id": review["id"],
                    "status": "pending",
                    "category": category,
                    "confidence": confidence,
                    "rationale": rationale,
                }
            )
            state_messages.append(
                AIMessage(
                    content=f"Low-confidence triage flagged for review {review.get('id')}."
                )
            )

        audit_log.append(
            {
                "timestamp": utc_timestamp(),
                "event": "triage_decision",
                "review_id": review.get("id"),
                "details": {
                    "category": category,
                    "confidence": confidence,
                    "low_confidence": low_confidence,
                    "language": language,
                },
            }
        )

    summary = (
        "Triage complete: "
        f"{len(bug_reviews)} bugs, "
        f"{len(feature_reviews)} features, "
        f"{len(praise_reviews)} praise."
    )

    state_messages.append(AIMessage(content=summary))

    return {
        "triage_results": triage_results,
        "bug_reviews": bug_reviews,
        "feature_reviews": feature_reviews,
        "praise_reviews": praise_reviews,
        "triage_needs_review": triage_needs_review,
        "processing_errors": processing_errors,
        "review_queue": review_queue,
        "audit_log": audit_log,
        "messages": state_messages,
    }


def route_review(state: ReviewState) -> list[str] | str:
    """Route to the appropriate handler based on classification.

    TODO: Implement this routing function.

    This function is used by conditional_edges to determine
    which node to execute next.

    Args:
        state: Current state with classification

    Returns:
        Name of the next node: "bug_reporter", "feature_analyst", or "praise_logger"
    """
    bug_reviews = state.get("bug_reviews", [])
    feature_reviews = state.get("feature_reviews", [])
    praise_reviews = state.get("praise_reviews", [])

    routes: list[str] = []
    if bug_reviews:
        routes.append("bug_reporter")
    if feature_reviews:
        routes.append("feature_analyst")
    if praise_reviews:
        routes.append("praise_logger")

    if not routes:
        return "summary"

    return routes
