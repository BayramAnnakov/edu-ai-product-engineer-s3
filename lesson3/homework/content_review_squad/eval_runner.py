"""Evaluation runner for Content Review Squad."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from .graph import create_content_review_squad
from .state import Review


REQUIRED_FEATURE_FIELDS = [
    "feature_name",
    "problem",
    "proposed_solution",
    "priority",
    "impact",
    "effort",
]


def load_eval_data(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_prediction_maps(state: dict) -> dict:
    triage_by_id = {item.get("id"): item for item in state.get("triage_results", [])}
    bug_by_id = {
        item.get("id"): item.get("details", {}).get("bug_report", {})
        for item in state.get("bug_results", [])
    }
    feature_by_id = {
        item.get("id"): item.get("details", {}).get("feature_spec", {})
        for item in state.get("feature_results", [])
    }
    praise_by_id = {
        item.get("id"): item.get("details", {}).get("testimonial", {})
        for item in state.get("praise_results", [])
    }
    return {
        "triage": triage_by_id,
        "bug": bug_by_id,
        "feature": feature_by_id,
        "praise": praise_by_id,
    }


def compute_metrics(cases: list[dict], predictions: dict) -> dict:
    confusion = defaultdict(lambda: defaultdict(int))
    per_case = []

    total = len(cases)
    correct = 0
    bug_cases = 0
    bug_severity_hits = 0
    feature_cases = 0
    feature_complete = 0
    praise_cases = 0
    praise_complete = 0
    missing_triage = 0

    triage_by_id = predictions["triage"]
    bug_by_id = predictions["bug"]
    feature_by_id = predictions["feature"]
    praise_by_id = predictions["praise"]

    per_category_totals = defaultdict(int)
    per_category_correct = defaultdict(int)

    for case in cases:
        review = case.get("review", {})
        expected = case.get("expected", {})
        review_id = review.get("id")
        expected_category = expected.get("category")
        per_category_totals[expected_category] += 1

        triage = triage_by_id.get(review_id)
        predicted_category = triage.get("category") if triage else None
        if not triage:
            missing_triage += 1

        if predicted_category:
            confusion[expected_category][predicted_category] += 1
        else:
            confusion[expected_category]["missing"] += 1

        category_match = predicted_category == expected_category
        if category_match:
            correct += 1
            per_category_correct[expected_category] += 1

        severity_match = None
        if expected_category == "bug":
            bug_cases += 1
            expected_severities = expected.get("severity", [])
            predicted_severity = bug_by_id.get(review_id, {}).get("severity")
            if expected_severities:
                severity_match = predicted_severity in expected_severities
                if severity_match:
                    bug_severity_hits += 1

        feature_complete_flag = None
        if expected_category == "feature":
            feature_cases += 1
            spec = feature_by_id.get(review_id, {})
            feature_complete_flag = all(spec.get(field) for field in REQUIRED_FEATURE_FIELDS)
            if feature_complete_flag:
                feature_complete += 1

        praise_complete_flag = None
        if expected_category == "praise":
            praise_cases += 1
            testimonial = praise_by_id.get(review_id, {})
            praise_complete_flag = bool(testimonial.get("quote")) and (
                testimonial.get("sentiment_score") is not None
            )
            if praise_complete_flag:
                praise_complete += 1

        per_case.append(
            {
                "id": case.get("id"),
                "review_id": review_id,
                "expected_category": expected_category,
                "predicted_category": predicted_category,
                "category_match": category_match,
                "severity_match": severity_match,
                "feature_spec_complete": feature_complete_flag,
                "praise_complete": praise_complete_flag,
            }
        )

    category_accuracy = correct / total if total else 0.0
    per_category_accuracy = {
        category: (per_category_correct[category] / per_category_totals[category])
        if per_category_totals[category]
        else 0.0
        for category in per_category_totals
    }

    metrics = {
        "total_cases": total,
        "category_accuracy": round(category_accuracy, 3),
        "per_category_accuracy": {
            key: round(value, 3) for key, value in per_category_accuracy.items()
        },
        "missing_triage": missing_triage,
        "bug_severity_match_rate": round(
            (bug_severity_hits / bug_cases) if bug_cases else 0.0, 3
        ),
        "feature_spec_completeness": round(
            (feature_complete / feature_cases) if feature_cases else 0.0, 3
        ),
        "praise_completeness": round(
            (praise_complete / praise_cases) if praise_cases else 0.0, 3
        ),
        "confusion_matrix": {
            expected: dict(predicted)
            for expected, predicted in confusion.items()
        },
    }

    return {"metrics": metrics, "cases": per_case}


async def run_eval(data_path: str) -> dict:
    data = load_eval_data(data_path)
    cases = data.get("cases", [])
    reviews: list[Review] = [case.get("review") for case in cases]

    graph = create_content_review_squad()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    config = {"configurable": {"thread_id": f"content-review-eval-{timestamp}"}}

    initial_state = {
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
    predictions = build_prediction_maps(result)
    return compute_metrics(cases, predictions)


def main():
    parser = argparse.ArgumentParser(description="Content Review Squad Eval Runner")
    parser.add_argument(
        "--data",
        type=str,
        default="eval_data.json",
        help="Path to evaluation dataset JSON",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="Optional path to save evaluation report JSON",
    )
    args = parser.parse_args()

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
        raise SystemExit("Set OPENAI_API_KEY or OPENROUTER_API_KEY before running evals.")

    report = asyncio.run(run_eval(args.data))
    print("\n=== Eval Summary ===")
    for key, value in report["metrics"].items():
        print(f"{key}: {value}")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
        print(f"\nSaved eval report to: {args.out}")


if __name__ == "__main__":
    main()
