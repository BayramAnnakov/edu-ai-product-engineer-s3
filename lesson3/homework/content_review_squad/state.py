"""State definition for the Content Review Squad.

TODO: Extend this state schema with all the fields you need.

Hints:
- Think about what each agent needs to read and write
- Consider using sub-TypedDicts for structured data
- Remember to use Annotated[list, add_messages] for conversation history
"""

import operator

from typing import TypedDict, Literal, Annotated, NotRequired
from langgraph.graph import add_messages


class Review(TypedDict):
    """A single review to process."""
    id: int
    text: str
    rating: int
    raw_text: NotRequired[str]
    language: NotRequired[str]
    source: NotRequired[str]
    metadata: NotRequired[dict]


class ReviewResult(TypedDict, total=False):
    """Result of processing a single review."""
    id: int
    category: Literal["bug", "feature", "praise"]
    action_taken: str
    details: dict


class TriageResult(TypedDict, total=False):
    """Classification result for a single review."""
    id: int
    category: Literal["bug", "feature", "praise"]
    confidence: float
    language: str
    rationale: str
    low_confidence: bool


class BugReport(TypedDict, total=False):
    """Structured bug report extracted from a review."""
    summary: str
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str
    severity: Literal["critical", "high", "medium", "low"]


class FeatureSpec(TypedDict, total=False):
    """Feature specification generated from a request."""
    feature_name: str
    problem: str
    proposed_solution: str
    user_benefit: str
    complexity: Literal["low", "medium", "high"]
    priority: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]
    effort: Literal["low", "medium", "high"]
    success_metrics: list[str]
    confidence: float
    pending_approval: bool
    approved: bool | None
    rejection_reason: str | None


class Testimonial(TypedDict, total=False):
    """Testimonial extracted from praise reviews."""
    quote: str
    sentiment_summary: str
    value_rating: Literal["high", "medium", "low"]
    suggested_usage: str
    sentiment_score: float


class SummaryStats(TypedDict, total=False):
    """Summary statistics for processed reviews."""
    total_reviews: int
    bugs_count: int
    features_count: int
    praise_count: int
    pending_feature_count: int
    avg_triage_confidence: float
    low_confidence_count: int
    severity_distribution: dict[str, int]
    feature_priority_distribution: dict[str, int]
    approval_rate: float
    top_clusters: list["TopicCluster"]
    review_queue_size: int
    triage_review_count: int
    feature_approval_pending: int


class TopicCluster(TypedDict, total=False):
    """Clustered theme summary across reviews."""
    id: str
    category: Literal["bug", "feature", "praise"]
    label: str
    count: int
    item_ids: list[int]
    keywords: list[str]
    sample_texts: list[str]
    priority_score: float


class ReviewQueueItem(TypedDict, total=False):
    """Item awaiting human review or approval."""
    type: Literal["triage", "feature_approval"]
    review_id: int
    status: str
    category: str
    confidence: float
    rationale: str
    feature_name: str
    priority: str
    impact: str
    effort: str


class AuditEvent(TypedDict, total=False):
    """Audit log event emitted by nodes."""
    timestamp: str
    event: str
    review_id: int
    details: dict


class ReviewState(TypedDict, total=False):
    """The shared state for the Content Review Squad.

    TODO: Add more fields as needed for your implementation.

    Consider organizing into sections:
    - INPUT: Reviews to process
    - TRIAGE: Classification results
    - AGENT RESULTS: What each specialist produces
    - HUMAN REVIEW: Approval status
    - SYNTHESIS: Final summary
    - MESSAGES: Conversation history
    """

    # === INPUT ===
    reviews: list[Review]
    current_review: Review | None  # The review currently being processed

    # === TRIAGE ===
    triage_results: list[TriageResult]
    bug_reviews: list[Review]
    feature_reviews: list[Review]
    praise_reviews: list[Review]
    triage_needs_review: list[TriageResult]

    # === AGENT RESULTS ===
    bug_results: list[ReviewResult]
    feature_results: list[ReviewResult]
    praise_results: list[ReviewResult]

    # === HUMAN REVIEW ===
    pending_features: list[ReviewResult]
    approved_features: list[ReviewResult]
    rejected_features: list[ReviewResult]

    # === SYNTHESIS ===
    summary_report: str
    statistics: SummaryStats
    processing_errors: Annotated[list[dict], operator.add]
    topic_clusters: list[TopicCluster]
    review_queue: Annotated[list[ReviewQueueItem], operator.add]
    audit_log: Annotated[list[AuditEvent], operator.add]

    # === MESSAGES ===
    # Use add_messages reducer for conversation history
    messages: Annotated[list, add_messages]
