"""Summary Node - Aggregates all processed reviews into a report.

TODO: Implement this node to:
1. Collect results from all branches (bugs, features, praise)
2. Generate statistics
3. Create a summary report
"""

import json

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..analysis import cluster_items, freq_boost, weighted_score
from ..llm import get_chat_model
from ..state import ReviewState


SUMMARY_PROMPT = """You are a review processing summary writer. Your job is to:

1. Summarize the results from processing multiple reviews
2. Provide counts by category (bugs, features, praise)
3. Highlight key actions taken
4. Note any items pending human review

Format the summary in a clear, executive-friendly way.
"""


async def summary_node(state: ReviewState) -> dict:
    """Generate a summary of all processed reviews.

    TODO: Implement this function.

    This node is the fan-in point where all branches converge.
    It should aggregate results from:
    - bug_results
    - feature_results (both approved and pending)
    - praise_results

    Steps:
    1. Collect all results from state
    2. Calculate statistics
    3. Use LLM to generate readable summary
    4. Return final state with summary

    Args:
        state: Current review state with all results

    Returns:
        State update with summary report
    """
    bug_results = state.get("bug_results", [])
    feature_results = state.get("feature_results", [])
    praise_results = state.get("praise_results", [])
    pending_features = state.get("pending_features", [])
    approved_features = state.get("approved_features", [])
    rejected_features = state.get("rejected_features", [])
    triage_results = state.get("triage_results", [])
    bug_reviews = state.get("bug_reviews", [])
    feature_reviews = state.get("feature_reviews", [])
    praise_reviews = state.get("praise_reviews", [])
    review_queue = state.get("review_queue", [])

    total_reviews = (
        len(state.get("reviews", []))
        or (len(bug_results) + len(feature_results) + len(praise_results))
    )
    bugs_count = len(bug_results)
    features_count = len(feature_results)
    praise_count = len(praise_results)
    pending_feature_count = len(pending_features)

    severity_distribution: dict[str, int] = {}
    for item in bug_results:
        severity = (
            item.get("details", {})
            .get("bug_report", {})
            .get("severity", "unknown")
        )
        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

    feature_priority_distribution: dict[str, int] = {}
    for item in feature_results:
        priority = (
            item.get("details", {})
            .get("feature_spec", {})
            .get("priority", "unknown")
        )
        feature_priority_distribution[priority] = (
            feature_priority_distribution.get(priority, 0) + 1
        )

    confidence_values = [
        result.get("confidence")
        for result in triage_results
        if isinstance(result.get("confidence"), (int, float))
    ]
    avg_triage_confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    )
    low_confidence_count = len(
        [result for result in triage_results if result.get("low_confidence")]
    )

    approvals_total = len(approved_features) + len(rejected_features)
    approval_rate = len(approved_features) / approvals_total if approvals_total else 0.0

    latest_queue: dict[tuple[str, int], dict] = {}
    for item in review_queue:
        queue_type = item.get("type")
        review_id = item.get("review_id")
        if queue_type and review_id is not None:
            latest_queue[(queue_type, review_id)] = item

    pending_queue = [
        item for item in latest_queue.values() if item.get("status") == "pending"
    ]
    review_queue_size = len(pending_queue)
    triage_review_count = len(
        [item for item in pending_queue if item.get("type") == "triage"]
    )
    feature_approval_pending = len(
        [item for item in pending_queue if item.get("type") == "feature_approval"]
    )

    review_map = {review.get("id"): review for review in state.get("reviews", [])}
    bug_reports_by_id = {
        item.get("id"): item.get("details", {}).get("bug_report", {})
        for item in bug_results
    }
    feature_specs_by_id = {
        item.get("id"): item.get("details", {}).get("feature_spec", {})
        for item in feature_results
    }
    testimonials_by_id = {
        item.get("id"): item.get("details", {}).get("testimonial", {})
        for item in praise_results
    }

    severity_weight = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
    }
    priority_weight = {"high": 1.0, "medium": 0.6, "low": 0.3}
    effort_weight = {"low": 1.0, "medium": 0.8, "high": 0.6}

    def bug_score(items: list[dict]) -> float:
        scores = []
        for item in items:
            report = bug_reports_by_id.get(item.get("id"), {})
            severity = str(report.get("severity", "medium")).lower()
            scores.append(severity_weight.get(severity, 0.5))
        return weighted_score(scores) * freq_boost(len(items))

    def feature_score(items: list[dict]) -> float:
        scores = []
        for item in items:
            spec = feature_specs_by_id.get(item.get("id"), {})
            priority = priority_weight.get(str(spec.get("priority", "medium")).lower(), 0.6)
            impact = priority_weight.get(str(spec.get("impact", "medium")).lower(), 0.6)
            effort = effort_weight.get(str(spec.get("effort", "medium")).lower(), 0.8)
            confidence = spec.get("confidence", 0.6)
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 0.6
            scores.append((priority * 0.45 + impact * 0.4 + confidence * 0.15) * effort)
        return weighted_score(scores) * freq_boost(len(items))

    def praise_score(items: list[dict]) -> float:
        rating_weight = {"high": 1.0, "medium": 0.6, "low": 0.3}
        scores = []
        for item in items:
            testimonial = testimonials_by_id.get(item.get("id"), {})
            value_rating = rating_weight.get(
                str(testimonial.get("value_rating", "medium")).lower(), 0.6
            )
            sentiment = testimonial.get("sentiment_score", 0.6)
            try:
                sentiment = float(sentiment)
            except (TypeError, ValueError):
                sentiment = 0.6
            scores.append(value_rating * 0.6 + sentiment * 0.4)
        return weighted_score(scores) * freq_boost(len(items))

    bug_items = bug_reviews or [review_map[item.get("id")] for item in bug_results if review_map.get(item.get("id"))]
    feature_items = feature_reviews or [review_map[item.get("id")] for item in feature_results if review_map.get(item.get("id"))]
    praise_items = praise_reviews or [review_map[item.get("id")] for item in praise_results if review_map.get(item.get("id"))]

    topic_clusters = []
    if bug_items:
        topic_clusters.extend(
            cluster_items(bug_items, lambda item: item.get("text", ""), category="bug", score_fn=bug_score)
        )
    if feature_items:
        topic_clusters.extend(
            cluster_items(
                feature_items,
                lambda item: item.get("text", ""),
                category="feature",
                score_fn=feature_score,
            )
        )
    if praise_items:
        topic_clusters.extend(
            cluster_items(
                praise_items,
                lambda item: item.get("text", ""),
                category="praise",
                score_fn=praise_score,
            )
        )

    topic_clusters.sort(key=lambda item: item.get("priority_score", 0.0), reverse=True)

    stats = {
        "total_reviews": total_reviews,
        "bugs_count": bugs_count,
        "features_count": features_count,
        "praise_count": praise_count,
        "pending_feature_count": pending_feature_count,
        "avg_triage_confidence": avg_triage_confidence,
        "low_confidence_count": low_confidence_count,
        "severity_distribution": severity_distribution,
        "feature_priority_distribution": feature_priority_distribution,
        "approval_rate": approval_rate,
        "review_queue_size": review_queue_size,
        "triage_review_count": triage_review_count,
        "feature_approval_pending": feature_approval_pending,
        "top_clusters": [
            {
                "id": cluster.get("id"),
                "category": cluster.get("category"),
                "label": cluster.get("label"),
                "count": cluster.get("count"),
                "priority_score": cluster.get("priority_score"),
            }
            for cluster in topic_clusters[:6]
        ],
    }

    context = {
        "statistics": stats,
        "bug_actions": [item.get("action_taken") for item in bug_results],
        "feature_actions": [item.get("action_taken") for item in feature_results],
        "praise_actions": [item.get("action_taken") for item in praise_results],
        "pending_features": [
            item.get("details", {}).get("feature_spec") for item in pending_features
        ],
        "triage_low_confidence": low_confidence_count,
        "severity_distribution": severity_distribution,
        "feature_priority_distribution": feature_priority_distribution,
        "approval_rate": approval_rate,
        "review_queue": {
            "pending_total": review_queue_size,
            "triage_review_count": triage_review_count,
            "feature_approval_pending": feature_approval_pending,
        },
        "top_clusters": stats["top_clusters"],
    }

    llm = get_chat_model("gpt-5-mini", temperature=0)
    prompt = (
        "Generate a concise executive summary of the review processing results. "
        "Use the statistics and actions provided. Highlight any pending approvals.\n\n"
        f"Context JSON:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )

    fallback_summary = (
        "Content Review Summary\n"
        f"Total Reviews: {total_reviews}\n"
        f"Bugs: {bugs_count}, Features: {features_count}, Praise: {praise_count}\n"
        f"Pending Feature Approvals: {pending_feature_count}\n"
        f"Avg Triage Confidence: {avg_triage_confidence:.2f}\n"
        f"Approval Rate: {approval_rate:.2f}\n"
        f"Review Queue Pending: {review_queue_size}"
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content=SUMMARY_PROMPT),
            HumanMessage(content=prompt),
        ])

        summary_report = (response.content or "").strip() or fallback_summary
    except Exception as exc:
        summary_report = fallback_summary
        return {
            "summary_report": summary_report,
            "statistics": stats,
            "topic_clusters": topic_clusters,
            "messages": [
                AIMessage(
                    content=(
                        "LLM unavailable for summary; used fallback summary "
                        f"({type(exc).__name__})."
                    )
                )
            ],
        }

    return {
        "summary_report": summary_report,
        "statistics": stats,
        "topic_clusters": topic_clusters,
        "messages": [AIMessage(content="Summary generated.")],
    }
