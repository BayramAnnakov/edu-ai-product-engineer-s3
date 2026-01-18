"""Graph assembly for the Content Review Squad.

TODO: Implement the graph wiring.

Key patterns to implement:
1. Triage node at entry
2. Conditional edges based on classification
3. Fan-in to summary node
4. Human-in-the-loop for feature approval
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ReviewState
from .nodes import (
    triage_node,
    bug_reporter_node,
    feature_analyst_node,
    praise_logger_node,
    summary_node,
)
from .nodes.triage import route_review


def create_content_review_squad(checkpointer=None, interrupt_after_feature: bool = False):
    """Create and compile the Content Review Squad graph.

    TODO: Implement this function.

    Architecture:
    ```
                        ┌─────────────────┐
                        │  Triage Agent   │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │    Bug    │ │  Feature  │ │   Praise  │
             │  Reporter │ │  Analyst  │ │   Logger  │
             └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                   │             │             │
                   │      [HUMAN REVIEW]       │
                   │             │             │
                   └─────────────┼─────────────┘
                                 ▼
                        ┌─────────────────┐
                        │     Summary     │
                        └─────────────────┘
    ```

    Steps:
    1. Create StateGraph with ReviewState
    2. Add all nodes
    3. Add edges from START to triage
    4. Add conditional edges from triage to handlers
    5. Add edges from handlers to summary
    6. Add edge from summary to END
    7. Compile with checkpointer
    8. For human-in-the-loop: use interrupt_before or interrupt_after

    Args:
        checkpointer: Optional checkpointer for persistence

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(ReviewState)

    # Add nodes
    graph.add_node("triage", triage_node)
    graph.add_node("bug_reporter", bug_reporter_node)
    graph.add_node("feature_analyst", feature_analyst_node)
    graph.add_node("praise_logger", praise_logger_node)
    graph.add_node("summary", summary_node)

    # Add entry edge
    graph.add_edge(START, "triage")

    # Conditional fan-out from triage
    graph.add_conditional_edges(
        "triage",
        route_review,
        {
            "bug_reporter": "bug_reporter",
            "feature_analyst": "feature_analyst",
            "praise_logger": "praise_logger",
            "summary": "summary",
        },
    )

    # Fan-in to summary
    graph.add_edge("bug_reporter", "summary")
    graph.add_edge("feature_analyst", "summary")
    graph.add_edge("praise_logger", "summary")

    # Exit
    graph.add_edge("summary", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    if interrupt_after_feature:
        return graph.compile(
            checkpointer=checkpointer,
            interrupt_after=["feature_analyst"],
        )

    return graph.compile(checkpointer=checkpointer)


# Convenience instance (students should implement create_content_review_squad first)
# content_review_squad = create_content_review_squad()
