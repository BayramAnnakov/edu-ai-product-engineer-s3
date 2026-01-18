# Content Review Squad — Technical Overview

## 1) Architecture
The system is a LangGraph StateGraph with fan-out/fan-in routing:

```
START → triage → (bug_reporter | feature_analyst | praise_logger) → summary → END
                         ↑
                  [human review]
```

- **triage**: classification + confidence + language
- **bug_reporter**: structured bug report + simulated issue creation
- **feature_analyst**: feature spec + impact/effort scoring + approval queue
- **praise_logger**: testimonial extraction + sentiment scoring
- **summary**: KPIs + clustering + executive summary

---

## 2) State Model (ReviewState)
Key fields:
- **triage_results**, **bug_results**, **feature_results**, **praise_results**
- **pending_features**, **approved_features**, **rejected_features**
- **review_queue** (pending triage/feature approvals)
- **audit_log** (timestamped decision trail)
- **statistics** (KPI summary)
- **topic_clusters** (Phase 2 analytics)

Reducers:
- `processing_errors` and `audit_log` are aggregated with `Annotated[..., operator.add]`.

---

## 3) LLM Hardening
- Centralized model config: `llm.get_chat_model` (OpenAI or OpenRouter).
- Robust JSON parsing: `parsing.parse_json_dict` to handle malformed output.
- Fallback heuristics for continuity if LLM fails.

---

## 4) Phase 2 Analytics
**Clustering + prioritization** in `analysis.py`:
- Tokenization + Jaccard similarity for dedupe.
- `cluster_items()` builds topic clusters with keywords + samples.
- `weighted_score()` and `freq_boost()` prioritize clusters.

---

## 5) Phase 3 Operations
**Review Queue**
- Low-confidence triage items are queued.
- Feature specs are queued for approval.

**Audit Log**
- Every decision/action generates a timestamped audit event.
- Events include triage decisions, bug reports, feature drafts, approvals, rejections.

---

## 6) Exports
- **JSON**: full state snapshot + clusters + audit log.
- **CSV**: flattened per-review rows with merged fields.

---

## 7) Evaluation Suite
Dataset: `content_review_squad/eval_data.json`

Run:
```bash
python -m content_review_squad.eval_runner \
  --data content_review_squad/eval_data.json \
  --out outputs/eval_report.json
```
Outputs:
- category accuracy
- per-category accuracy
- bug severity match rate
- feature spec completeness
- praise completeness
- confusion matrix

---

## 8) How to run
**Main flow:**
```bash
python -m content_review_squad.main \
  --export-json outputs/results.json \
  --export-csv outputs/results.csv
```

**Interactive approvals:**
```bash
python -m content_review_squad.main --interactive
```

---

## 9) Environment
Required:
- `OPENAI_API_KEY` **or** `OPENROUTER_API_KEY`

Optional (observability):
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_PROJECT=content-review-squad`
- `LANGCHAIN_API_KEY` (LangSmith)

---

## 10) Extensibility
- Add new agent nodes (e.g., churn risk, pricing feedback).
- Swap clustering algorithm for embeddings when volume increases.
- Replace simulated issue creation with real integrations.

---

## 11) Files of interest
- `nodes/triage.py`, `nodes/bug_reporter.py`, `nodes/feature_analyst.py`, `nodes/praise_logger.py`
- `nodes/summary.py`
- `analysis.py` (clustering + scoring)
- `eval_runner.py`, `eval_data.json`
- `state.py`, `graph.py`, `main.py`
