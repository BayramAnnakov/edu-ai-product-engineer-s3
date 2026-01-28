"""Lightweight clustering and scoring utilities for review analytics."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable, Iterable

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "to",
    "of",
    "in",
    "on",
    "it",
    "is",
    "are",
    "a",
    "an",
    "be",
    "as",
    "at",
    "by",
    "from",
    "or",
    "we",
    "you",
    "i",
    "my",
    "our",
    "app",
    "feature",
    "please",
    "would",
    "love",
    "add",
    "can",
    "could",
    "your",
    "не",
    "что",
    "это",
    "как",
    "мне",
    "мы",
    "вы",
    "они",
    "просто",
    "очень",
}

TOKEN_RE = re.compile(r"[\w']+")


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text or "")]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def jaccard_similarity(tokens_a: Iterable[str], tokens_b: Iterable[str]) -> float:
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def cluster_items(
    items: list,
    get_text: Callable[[dict], str],
    *,
    category: str,
    similarity_threshold: float = 0.35,
    max_keywords: int = 6,
    max_samples: int = 3,
    score_fn: Callable[[list], float] | None = None,
) -> list[dict]:
    clusters: list[dict] = []

    for item in items:
        text = get_text(item) or ""
        tokens = tokenize(text)
        if not tokens:
            continue

        best_cluster = None
        best_score = 0.0
        for cluster in clusters:
            score = jaccard_similarity(tokens, cluster["token_set"])
            if score > best_score:
                best_score = score
                best_cluster = cluster

        if best_cluster and best_score >= similarity_threshold:
            best_cluster["items"].append(item)
            best_cluster["token_set"].update(tokens)
            best_cluster["token_counts"].update(tokens)
            if len(best_cluster["sample_texts"]) < max_samples:
                best_cluster["sample_texts"].append(text[:160])
            best_cluster["item_ids"].append(item.get("id"))
        else:
            clusters.append({
                "items": [item],
                "token_set": set(tokens),
                "token_counts": Counter(tokens),
                "sample_texts": [text[:160]],
                "item_ids": [item.get("id")],
            })

    output: list[dict] = []
    for index, cluster in enumerate(clusters, start=1):
        keywords = [token for token, _ in cluster["token_counts"].most_common(max_keywords)]
        label = " ".join(keywords[:2]).title() if keywords else category.title()
        score = score_fn(cluster["items"]) if score_fn else 0.0
        output.append({
            "id": f"{category}-{index}",
            "category": category,
            "label": label,
            "count": len(cluster["items"]),
            "item_ids": cluster["item_ids"],
            "keywords": keywords,
            "sample_texts": cluster["sample_texts"],
            "priority_score": round(score, 3),
        })

    output.sort(key=lambda item: item.get("priority_score", 0.0), reverse=True)
    return output


def weighted_score(values: list[float], weight: float = 1.0) -> float:
    if not values:
        return 0.0
    return (sum(values) / len(values)) * weight


def freq_boost(count: int) -> float:
    return 1.0 + math.log(1 + count)
