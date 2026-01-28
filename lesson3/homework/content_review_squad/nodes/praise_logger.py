"""Praise Logger Node - Records positive feedback as testimonials.

TODO: Implement this node to:
1. Take a positive review from state
2. Extract key quotes and sentiment
3. Format as a testimonial
4. Return the result in state
"""

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..audit import utc_timestamp
from ..llm import get_chat_model
from ..parsing import parse_json_dict
from ..state import ReviewState


PRAISE_LOGGER_PROMPT = """You are a testimonial curator. Your job is to:

1. Extract the most impactful quote from the positive review
2. Summarize the key positive sentiment
3. Rate the testimonial value (high/medium/low)
4. Suggest where this testimonial could be used (landing page, social, etc.)
5. Provide a sentiment score between 0 and 1

Keep the original voice of the user when extracting quotes.
"""


async def praise_logger_node(state: ReviewState) -> dict:
    """Log positive feedback as a testimonial.

    TODO: Implement this function.

    Steps:
    1. Get the positive review from state
    2. Use LLM to extract and format testimonial (gpt-5-mini is fine)
    3. Return state update with testimonial

    Args:
        state: Current review state

    Returns:
        State update with testimonial result
    """
    praise_reviews = state.get("praise_reviews") or []
    current_review = state.get("current_review")

    if not praise_reviews and current_review:
        praise_reviews = [current_review]

    if not praise_reviews:
        return {
            "messages": [AIMessage(content="No praise reviews to log.")]
        }

    llm = get_chat_model("gpt-5-mini", temperature=0)
    praise_results = state.get("praise_results", [])
    messages = []
    processing_errors = []
    audit_log = []

    def normalize_value_rating(value: str | None) -> str:
        text = (value or "").strip().lower()
        if "high" in text:
            return "high"
        if "low" in text:
            return "low"
        if "medium" in text:
            return "medium"
        return "medium"

    def clamp_score(value: float | None, fallback: float) -> float:
        if value is None:
            return fallback
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return fallback

    for review in praise_reviews:
        prompt = (
            "Return ONLY valid JSON with keys: quote, sentiment_summary, "
            "value_rating (high/medium/low), suggested_usage, sentiment_score (0-1).\n\n"
            f"Review ID: {review['id']}\n"
            f"Rating: {review['rating']}\n"
            f"Text: {review['text']}"
        )

        fallback_testimonial = {
            "quote": review["text"],
            "sentiment_summary": "Positive feedback",
            "value_rating": "medium",
            "suggested_usage": "Marketing materials",
            "sentiment_score": min(max((review.get("rating", 3) / 5), 0.0), 1.0),
        }

        try:
            response = await llm.ainvoke([
                SystemMessage(content=PRAISE_LOGGER_PROMPT),
                HumanMessage(content=prompt),
            ])

            parsed = parse_json_dict(response.content or "")
            testimonial = parsed if parsed else fallback_testimonial
        except Exception as exc:
            testimonial = fallback_testimonial
            processing_errors.append(
                {
                    "node": "praise_logger",
                    "review_id": review.get("id"),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            messages.append(
                AIMessage(
                    content=(
                        "LLM unavailable for praise logging; used heuristic fallback "
                        f"for review {review.get('id')}. ({type(exc).__name__})"
                    )
                )
            )

        testimonial["value_rating"] = normalize_value_rating(
            testimonial.get("value_rating")
        )
        testimonial["sentiment_score"] = clamp_score(
            testimonial.get("sentiment_score"), fallback_testimonial["sentiment_score"]
        )

        praise_results.append({
            "id": review["id"],
            "category": "praise",
            "action_taken": "Logged testimonial",
            "details": {
                "testimonial": testimonial,
            },
        })

        audit_log.append(
            {
                "timestamp": utc_timestamp(),
                "event": "praise_logged",
                "review_id": review.get("id"),
                "details": {
                    "value_rating": testimonial.get("value_rating"),
                    "sentiment_score": testimonial.get("sentiment_score"),
                    "suggested_usage": testimonial.get("suggested_usage"),
                },
            }
        )

        messages.append(AIMessage(content=f"Praise logged for review {review['id']}."))

    return {
        "praise_results": praise_results,
        "processing_errors": processing_errors,
        "audit_log": audit_log,
        "messages": messages,
    }
