"""Main runner for the Content Review Squad homework.

Usage:
    python main.py

With human-in-the-loop demo:
    python main.py --interactive
"""

import asyncio
import argparse
import csv
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangSmith configuration
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "content-review-squad")

from .audit import utc_timestamp
from .graph import create_content_review_squad
from .state import ReviewState, Review


# Sample reviews for testing
SAMPLE_REVIEWS: list[Review] = [
    {
        "id": 1,
        "text": "App crashes every time I try to export to PDF. This is really frustrating!",
        "rating": 1,
    },
    {
        "id": 2,
        "text": "Would love to see a dark mode option. My eyes hurt using the app at night.",
        "rating": 4,
    },
    {
        "id": 3,
        "text": "Absolutely love this app! It's changed how I manage my projects. Best purchase ever!",
        "rating": 5,
    },
    {
        "id": 4,
        "text": "The login button doesn't work on Safari browser. Please fix ASAP.",
        "rating": 2,
    },
    {
        "id": 5,
        "text": "Can you add integration with Notion? That would be amazing for my workflow.",
        "rating": 4,
    },
]


async def process_reviews(reviews: list[Review], interactive: bool = False) -> ReviewState:
    """Process a batch of reviews through the Content Review Squad.

    TODO: Implement the review processing loop.

    For this homework, you might want to:
    1. Process reviews one at a time (simpler)
    2. Or process all at once and handle routing (more complex)

    Args:
        reviews: List of reviews to process
        interactive: If True, pause for human review on feature requests

    Returns:
        Final state with all results
    """
    print("\n" + "=" * 60)
    print("CONTENT REVIEW SQUAD")
    print("=" * 60)
    print(f"\nProcessing {len(reviews)} reviews...")

    graph = create_content_review_squad(interrupt_after_feature=interactive)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    config = {
        "configurable": {
            "thread_id": f"content-review-{timestamp}",
        }
    }

    initial_state: ReviewState = {
        "reviews": reviews,
        "current_review": None,
        "triage_results": [],
        "bug_reviews": [],
        "feature_reviews": [],
        "praise_reviews": [],
        "triage_needs_review": [],
        "bug_results": [],
        "feature_results": [],
        "praise_results": [],
        "pending_features": [],
        "approved_features": [],
        "rejected_features": [],
        "summary_report": "",
        "statistics": {},
        "processing_errors": [],
        "topic_clusters": [],
        "review_queue": [],
        "audit_log": [],
        "messages": [],
    }

    result = await graph.ainvoke(initial_state, config)

    if interactive:
        state_snapshot = await graph.aget_state(config)

        if state_snapshot.next:
            pending_features = result.get("pending_features", [])
            if pending_features:
                print("\n" + "-" * 60)
                print("HUMAN REVIEW REQUIRED: Feature Requests")
                print("-" * 60)

                approved_features = []
                rejected_features = []
                feature_results = result.get("feature_results", [])
                review_queue_updates = []
                audit_events = []

                for item in pending_features:
                    spec = item.get("details", {}).get("feature_spec", {})
                    feature_name = spec.get("feature_name", f"Feature #{item.get('id')}")
                    problem = spec.get("problem", "")
                    solution = spec.get("proposed_solution", "")

                    print(f"\nFeature: {feature_name}")
                    if problem:
                        print(f"Problem: {problem}")
                    if solution:
                        print(f"Proposed solution: {solution}")

                    decision = input("Approve this feature? [y/n]: ").strip().lower()
                    if decision in {"y", "yes"}:
                        spec["approved"] = True
                        spec["pending_approval"] = False
                        item["action_taken"] = "Approved by human reviewer"
                        approved_features.append(item)
                        review_queue_updates.append(
                            {
                                "type": "feature_approval",
                                "review_id": item.get("id"),
                                "status": "approved",
                                "category": "feature",
                                "feature_name": spec.get("feature_name"),
                                "priority": spec.get("priority"),
                                "impact": spec.get("impact"),
                                "effort": spec.get("effort"),
                                "confidence": spec.get("confidence"),
                                "rationale": spec.get("problem", ""),
                            }
                        )
                        audit_events.append(
                            {
                                "timestamp": utc_timestamp(),
                                "event": "feature_approved",
                                "review_id": item.get("id"),
                                "details": {
                                    "feature_name": spec.get("feature_name"),
                                    "priority": spec.get("priority"),
                                },
                            }
                        )
                    else:
                        reason = input("Reason for rejection: ").strip() or "Not specified"
                        spec["approved"] = False
                        spec["pending_approval"] = False
                        spec["rejection_reason"] = reason
                        item["action_taken"] = f"Rejected by human reviewer: {reason}"
                        rejected_features.append(item)
                        review_queue_updates.append(
                            {
                                "type": "feature_approval",
                                "review_id": item.get("id"),
                                "status": "rejected",
                                "category": "feature",
                                "feature_name": spec.get("feature_name"),
                                "priority": spec.get("priority"),
                                "impact": spec.get("impact"),
                                "effort": spec.get("effort"),
                                "confidence": spec.get("confidence"),
                                "rationale": reason,
                            }
                        )
                        audit_events.append(
                            {
                                "timestamp": utc_timestamp(),
                                "event": "feature_rejected",
                                "review_id": item.get("id"),
                                "details": {
                                    "feature_name": spec.get("feature_name"),
                                    "reason": reason,
                                },
                            }
                        )

                    item.setdefault("details", {})["feature_spec"] = spec

                graph.update_state(
                    config,
                    {
                        "feature_results": feature_results,
                        "pending_features": [],
                        "approved_features": approved_features,
                        "rejected_features": rejected_features,
                        "review_queue": review_queue_updates,
                        "audit_log": audit_events,
                    },
                    as_node="feature_analyst",
                )

                print("\nResuming execution...")

            result = await graph.ainvoke(None, config)

    return result


def print_results(state: ReviewState):
    """Pretty print the processing results."""
    print("\n" + "=" * 60)
    print("PROCESSING RESULTS")
    print("=" * 60)

    stats = state.get("statistics", {})
    bug_results = state.get("bug_results", [])
    feature_results = state.get("feature_results", [])
    praise_results = state.get("praise_results", [])
    pending_features = state.get("pending_features", [])
    approved_features = state.get("approved_features", [])
    rejected_features = state.get("rejected_features", [])
    triage_needs_review = state.get("triage_needs_review", [])
    processing_errors = state.get("processing_errors", [])
    topic_clusters = state.get("topic_clusters", [])
    review_queue = state.get("review_queue", [])
    audit_log = state.get("audit_log", [])

    if stats:
        print("\n--- Summary Stats ---")
        print(f"Total Reviews: {stats.get('total_reviews')}")
        print(f"Bugs: {stats.get('bugs_count')}")
        print(f"Features: {stats.get('features_count')}")
        print(f"Praise: {stats.get('praise_count')}")
        print(f"Pending Features: {stats.get('pending_feature_count')}")
        if "avg_triage_confidence" in stats:
            print(f"Avg Triage Confidence: {stats.get('avg_triage_confidence'):.2f}")
        if "approval_rate" in stats:
            print(f"Approval Rate: {stats.get('approval_rate'):.2f}")
        if stats.get("severity_distribution"):
            print(f"Severity Distribution: {stats.get('severity_distribution')}")
        if stats.get("feature_priority_distribution"):
            print(
                "Feature Priority Distribution: "
                f"{stats.get('feature_priority_distribution')}"
            )

    if bug_results:
        print("\n--- Bug Reports ---")
        for item in bug_results:
            print(f"- Review {item['id']}: {item.get('action_taken')}")

    if feature_results:
        print("\n--- Feature Specs ---")
        for item in feature_results:
            status = item.get("action_taken", "Spec drafted")
            print(f"- Review {item['id']}: {status}")

    if pending_features:
        print("\n--- Pending Feature Approvals ---")
        for item in pending_features:
            spec = item.get("details", {}).get("feature_spec", {})
            print(f"- {spec.get('feature_name', 'Feature request')} (review {item['id']})")

    if triage_needs_review:
        print("\n--- Low-Confidence Triage (Review Queue) ---")
        for item in triage_needs_review:
            print(
                f"- Review {item.get('id')}: {item.get('category')} "
                f"(confidence {item.get('confidence')})"
            )

    if topic_clusters:
        print("\n--- Top Topic Clusters ---")
        for cluster in topic_clusters[:5]:
            print(
                f"- [{cluster.get('category')}] {cluster.get('label')} "
                f"(count {cluster.get('count')}, score {cluster.get('priority_score')})"
            )

    if review_queue:
        pending_queue = [item for item in review_queue if item.get("status") == "pending"]
        if pending_queue:
            print("\n--- Review Queue Summary ---")
            print(f"Pending items: {len(pending_queue)}")

    if approved_features:
        print("\n--- Approved Features ---")
        for item in approved_features:
            spec = item.get("details", {}).get("feature_spec", {})
            print(f"- {spec.get('feature_name', 'Feature request')} (review {item['id']})")

    if rejected_features:
        print("\n--- Rejected Features ---")
        for item in rejected_features:
            spec = item.get("details", {}).get("feature_spec", {})
            reason = spec.get("rejection_reason", "No reason")
            print(f"- {spec.get('feature_name', 'Feature request')} (review {item['id']}): {reason}")

    if praise_results:
        print("\n--- Testimonials ---")
        for item in praise_results:
            quote = item.get("details", {}).get("testimonial", {}).get("quote", "")
            print(f"- Review {item['id']}: {quote[:80]}")

    if processing_errors:
        print("\n--- Processing Errors ---")
        for item in processing_errors:
            print(
                f"- {item.get('node')} review {item.get('review_id')}: "
                f"{item.get('error_type')}"
            )

    summary = state.get("summary_report", "No summary available")
    print("\n--- Summary Report ---")
    print(summary)


def export_results_json(state: ReviewState, path: str):
    """Export results to JSON (excluding non-serializable message objects)."""
    payload = {
        "reviews": state.get("reviews", []),
        "triage_results": state.get("triage_results", []),
        "bug_results": state.get("bug_results", []),
        "feature_results": state.get("feature_results", []),
        "praise_results": state.get("praise_results", []),
        "pending_features": state.get("pending_features", []),
        "approved_features": state.get("approved_features", []),
        "rejected_features": state.get("rejected_features", []),
        "statistics": state.get("statistics", {}),
        "summary_report": state.get("summary_report", ""),
        "processing_errors": state.get("processing_errors", []),
        "topic_clusters": state.get("topic_clusters", []),
        "review_queue": state.get("review_queue", []),
        "audit_log": state.get("audit_log", []),
    }

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def export_results_csv(state: ReviewState, path: str):
    """Export flattened per-review results to CSV."""
    rows: list[dict] = []

    def add_row(result: dict, extra: dict):
        rows.append({
            "review_id": result.get("id"),
            "category": result.get("category"),
            "action_taken": result.get("action_taken"),
            **extra,
        })

    for item in state.get("bug_results", []):
        bug_report = item.get("details", {}).get("bug_report", {})
        add_row(item, {
            "summary": bug_report.get("summary"),
            "severity": bug_report.get("severity"),
            "confidence": bug_report.get("confidence"),
        })

    for item in state.get("feature_results", []):
        spec = item.get("details", {}).get("feature_spec", {})
        add_row(item, {
            "feature_name": spec.get("feature_name"),
            "priority": spec.get("priority"),
            "impact": spec.get("impact"),
            "effort": spec.get("effort"),
            "confidence": spec.get("confidence"),
        })

    for item in state.get("praise_results", []):
        testimonial = item.get("details", {}).get("testimonial", {})
        add_row(item, {
            "quote": testimonial.get("quote"),
            "value_rating": testimonial.get("value_rating"),
            "sentiment_score": testimonial.get("sentiment_score"),
        })

    if not rows:
        return

    preferred_fields = [
        "review_id",
        "category",
        "action_taken",
        "summary",
        "severity",
        "confidence",
        "feature_name",
        "priority",
        "impact",
        "effort",
        "quote",
        "value_rating",
        "sentiment_score",
    ]
    union_fields = {key for row in rows for key in row.keys()}
    extra_fields = [key for key in sorted(union_fields) if key not in preferred_fields]
    fieldnames = preferred_fields + extra_fields

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Content Review Squad")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable human-in-the-loop for feature requests"
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default="",
        help="Path to export results as JSON"
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        default="",
        help="Path to export results as CSV"
    )
    args = parser.parse_args()

    # Check API key
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
        print("ERROR: Set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file.")
        return

    # Process reviews
    result = asyncio.run(process_reviews(SAMPLE_REVIEWS, args.interactive))
    print_results(result)

    if args.export_json:
        export_results_json(result, args.export_json)
        print(f"\nExported JSON results to: {args.export_json}")

    if args.export_csv:
        export_results_csv(result, args.export_csv)
        print(f"Exported CSV results to: {args.export_csv}")

    # LangSmith trace info
    if os.getenv("LANGCHAIN_API_KEY"):
        print(f"\nView trace: https://smith.langchain.com")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'content-review-squad')}")


if __name__ == "__main__":
    main()
