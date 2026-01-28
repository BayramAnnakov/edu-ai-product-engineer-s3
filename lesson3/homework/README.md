# Homework 3: Content Review Squad

Build a multi-agent system that processes app/product reviews and routes them to specialized agents.

## Objective

Create a LangGraph-based Content Review Squad that:
1. **Triages** incoming reviews (bug report, feature request, or praise)
2. **Routes** to specialized agents based on classification
3. **Processes** each review type with appropriate actions
4. **Synthesizes** a summary of all processed reviews

## Architecture

```
                    ┌─────────────────┐
                    │  Triage Agent   │
                    │  (classifier)   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Bug Reporter   │  │ Feature Analyst │  │  Praise Logger  │
│ (GitHub issues) │  │ (spec writer)   │  │ (testimonials)  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         │             [HUMAN REVIEW]              │
         │                    │                    │
         └───────────────────┬┴───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │    Summary      │
                    │     Agent       │
                    └─────────────────┘
```

## Requirements

Your implementation MUST include:

1. **StateGraph with Typed State** (15 points)
   - [ ] Define `ReviewState` TypedDict
   - [ ] Include input, agent results, and control fields
   - [ ] Use proper type hints

2. **Triage Node with Conditional Routing** (20 points)
   - [ ] Classify reviews into: bug, feature, praise
   - [ ] Return routing decision to appropriate branch
   - [ ] Use LLM for classification

3. **At Least One Parallel Fan-out Pattern** (15 points)
   - [ ] Multiple agents should execute in parallel
   - [ ] Can be within a branch or across branches

4. **Human-in-the-Loop for Feature Requests** (20 points)
   - [ ] Interrupt before feature spec is finalized
   - [ ] Allow human to approve/reject feature
   - [ ] Resume execution after approval

5. **Synthesis Node** (15 points)
   - [ ] Aggregate results from all branches
   - [ ] Generate summary report
   - [ ] Count reviews by category

6. **LangSmith Tracing** (15 points)
   - [ ] Enable LangSmith tracing
   - [ ] Include screenshot of trace in submission
   - [ ] Show parallel execution in trace

## Sample Input

```python
reviews = [
    {"id": 1, "text": "App crashes when I try to export PDF", "rating": 1},
    {"id": 2, "text": "Would love to see dark mode support!", "rating": 4},
    {"id": 3, "text": "Best app ever! Love the new features", "rating": 5},
    {"id": 4, "text": "Login button doesn't work on Safari", "rating": 2},
]
```

## Expected Output

```
Content Review Summary
======================
Total Reviews: 4

Bugs (2):
- Created GitHub issue #123 for PDF export crash
- Created GitHub issue #124 for Safari login bug

Feature Requests (1):
- Dark mode support: APPROVED by human reviewer
  → Spec written to features/dark_mode.md

Praise (1):
- Added to testimonials database
```

## Getting Started

1. Copy the `content_review_squad/` directory to your workspace
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys
4. Start with `state.py` - define your state schema
5. Implement nodes one by one
6. Wire up the graph in `graph.py`
7. Test with `main.py`

## Starter Code

The `content_review_squad/` directory contains:
- `state.py` - Starter state definition (extend this)
- `nodes/` - Skeleton files for each node
- `graph.py` - Graph assembly skeleton
- `main.py` - Runner with sample reviews

## Grading Rubric

| Criteria | Points |
|----------|--------|
| Typed State with proper schema | 15 |
| Triage with conditional routing | 20 |
| Parallel fan-out pattern | 15 |
| Human-in-the-loop | 20 |
| Synthesis node | 15 |
| LangSmith trace screenshot | 15 |
| **Total** | **100** |

## Submission

Submit:
1. Your completed `content_review_squad/` directory
2. Screenshot of LangSmith trace showing multi-agent execution
3. Brief write-up (1 paragraph) explaining your design decisions

## Tips

- Start with the state schema - think about what each agent needs
- Test each node independently before wiring up the graph
- Use `gpt-5-mini` for simpler tasks (triage, logging) to save costs
- Use `gpt-5.2` for complex tasks (feature spec writing)
- Check LangSmith traces to debug routing issues

## Resources

- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [Conditional Edges](https://docs.langchain.com/oss/javascript/langgraph/graph-api#conditional-edges)
- [Human-in-the-Loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop#human-in-the-loop)
- Workshop 3 demo code in `lesson3/workspace/`
