"""Feature Analyst Node - Analyzes feature requests and writes specs.

TODO: Implement this node to:
1. Take a feature request review from state
2. Analyze the feature request
3. Generate a feature specification
4. This node should have HUMAN-IN-THE-LOOP before finalizing

IMPORTANT: This is where you implement the human-in-the-loop requirement!
"""

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..audit import utc_timestamp
from ..llm import get_chat_model
from ..parsing import parse_json_dict
from ..state import ReviewState


FEATURE_ANALYST_PROMPT = """You are a feature specification writer. Your job is to:

1. Analyze the feature request from a user review
2. Determine feasibility and value
3. Write a brief feature specification including:
   - Feature name
   - Problem it solves
   - Proposed solution
   - User benefit
   - Implementation complexity (low/medium/high)
   - Priority recommendation

Be concise and focus on business value and user impact.
"""


async def feature_analyst_node(state: ReviewState) -> dict:
    """Analyze a feature request and prepare a specification.

    TODO: Implement this function.

    IMPORTANT: This node should prepare the feature spec but NOT finalize it.
    The human-in-the-loop should happen BEFORE this node or AFTER to review
    the spec before it's added to the final results.

    Options for human-in-the-loop:
    1. Use interrupt_before in graph.compile() on this node
    2. Use interrupt_after on this node
    3. Add a separate "review" node after this one

    Steps:
    1. Get the feature request from state
    2. Use LLM to analyze and generate spec (use gpt-5.2 for quality)
    3. Return state update with the spec (marked as pending approval)

    Args:
        state: Current review state

    Returns:
        State update with feature spec (pending human approval)
    """
    feature_reviews = state.get("feature_reviews") or []
    current_review = state.get("current_review")

    if not feature_reviews and current_review:
        feature_reviews = [current_review]

    if not feature_reviews:
        return {
            "messages": [AIMessage(content="No feature requests to analyze.")]
        }

    llm = get_chat_model("gpt-5.2", temperature=0)
    feature_results = state.get("feature_results", [])
    pending_features = state.get("pending_features", [])
    messages = []
    processing_errors = []
    review_queue = []
    audit_log = []

    def normalize_level(value: str | None, fallback: str) -> str:
        text = (value or "").strip().lower()
        if "high" in text:
            return "high"
        if "low" in text:
            return "low"
        if "medium" in text:
            return "medium"
        return fallback

    def clamp_confidence(value: float | None, fallback: float) -> float:
        if value is None:
            return fallback
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return fallback

    for review in feature_reviews:
        prompt = (
            "Return ONLY valid JSON with keys: feature_name, problem, "
            "proposed_solution, user_benefit, complexity (low/medium/high), "
            "priority (low/medium/high), impact (low/medium/high), "
            "effort (low/medium/high), success_metrics (array), confidence (0-1).\n\n"
            f"Review ID: {review['id']}\n"
            f"Rating: {review['rating']}\n"
            f"Text: {review['text']}"
        )

        fallback_spec = {
            "feature_name": "Feature request",
            "problem": review["text"],
            "proposed_solution": "",
            "user_benefit": "",
            "complexity": "medium",
            "priority": "medium",
            "impact": "medium",
            "effort": "medium",
            "success_metrics": [],
            "confidence": 0.5,
        }

        try:
            response = await llm.ainvoke([
                SystemMessage(content=FEATURE_ANALYST_PROMPT),
                HumanMessage(content=prompt),
            ])

            parsed = parse_json_dict(response.content or "")
            spec = parsed if parsed else fallback_spec
        except Exception as exc:
            spec = fallback_spec
            processing_errors.append(
                {
                    "node": "feature_analyst",
                    "review_id": review.get("id"),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            messages.append(
                AIMessage(
                    content=(
                        "LLM unavailable for feature analysis; used heuristic fallback "
                        f"for review {review.get('id')}. ({type(exc).__name__})"
                    )
                )
            )

        spec["complexity"] = normalize_level(spec.get("complexity"), "medium")
        spec["priority"] = normalize_level(spec.get("priority"), "medium")
        spec["impact"] = normalize_level(spec.get("impact"), "medium")
        spec["effort"] = normalize_level(spec.get("effort"), "medium")
        spec["success_metrics"] = (
            spec.get("success_metrics")
            if isinstance(spec.get("success_metrics"), list)
            else []
        )
        spec["confidence"] = clamp_confidence(spec.get("confidence"), 0.6)

        spec.update({
            "pending_approval": True,
            "approved": None,
            "rejection_reason": None,
        })

        feature_result = {
            "id": review["id"],
            "category": "feature",
            "action_taken": "Spec drafted (pending approval)",
            "details": {
                "feature_spec": spec,
                "review": review,
            },
        }

        feature_results.append(feature_result)
        pending_features.append(feature_result)
        review_queue.append(
            {
                "type": "feature_approval",
                "review_id": review["id"],
                "status": "pending",
                "category": "feature",
                "feature_name": spec.get("feature_name", "Feature request"),
                "priority": spec.get("priority", "medium"),
                "impact": spec.get("impact", "medium"),
                "effort": spec.get("effort", "medium"),
                "confidence": spec.get("confidence", 0.6),
                "rationale": spec.get("problem", ""),
            }
        )
        audit_log.append(
            {
                "timestamp": utc_timestamp(),
                "event": "feature_spec_drafted",
                "review_id": review.get("id"),
                "details": {
                    "feature_name": spec.get("feature_name"),
                    "priority": spec.get("priority"),
                    "impact": spec.get("impact"),
                    "effort": spec.get("effort"),
                },
            }
        )
        messages.append(AIMessage(content=f"Feature spec drafted for review {review['id']}."))

    return {
        "feature_results": feature_results,
        "pending_features": pending_features,
        "processing_errors": processing_errors,
        "review_queue": review_queue,
        "audit_log": audit_log,
        "messages": messages,
    }


async def feature_approval_node(state: ReviewState) -> dict:
    """Handle human approval/rejection of feature specs.

    TODO (OPTIONAL): Implement a separate approval node.

    This is an alternative approach to using interrupt_before/after.
    You can have a dedicated node that checks approval status.

    Args:
        state: Current review state with pending feature spec

    Returns:
        State update with approved/rejected status
    """
    # This is optional - you can use interrupt_before/after instead
    raise NotImplementedError("Optional: Implement if using separate approval node")
