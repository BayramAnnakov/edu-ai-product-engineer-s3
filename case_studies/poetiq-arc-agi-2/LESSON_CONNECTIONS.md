# Lesson Connections: Poetiq ARC-AGI-2

How Poetiq's SOTA approach maps to course concepts.

---

## Lesson 2: Building Reliable Agents

### The Reflection Pattern

**Course Version (L2)**:
```
Turn 1: Generate V1 Research (initial)
         ↓
Turn 2: Collect External Feedback (human review)
         ↓
Turn 3: Reflect and Generate V2 (improved)
```

**Poetiq's Version**:
```
Iteration 1: Generate Python transform() function
         ↓
Iteration 2: Execute code, collect errors + soft scores
         ↓
Iteration 3-10: Feed errors back, generate improved code
```

**Key Difference**: Poetiq's reflection is **grounded in execution**. Instead of human feedback or LLM self-critique, they get ground-truth from running actual code. This eliminates hallucinated quality assessments.

### External Feedback Sources

| L2 Feedback Source | Poetiq Equivalent |
|--------------------|-------------------|
| Human-in-the-loop (CLI) | Code execution results |
| Data quality signals (EnrichLayer) | Soft scoring (pixel accuracy) |
| Quality assessment in tool response | Pass/fail on training examples |

**Lesson**: External feedback breaks the "prompt engineering plateau" — Poetiq proves this works at SOTA scale.

### Improved Tool Design

L2 teaches structured tool docstrings with:
- `USE WHEN` clauses
- `RETURNS ON SUCCESS/ERROR` sections

Poetiq's prompts use similar patterns:
- Explicit transformation taxonomies (Color, Spatial, Pattern)
- Clear output format requirements (`def transform(grid)`)
- Constraint specification (numpy only, no main blocks)

---

## Lesson 3: Multi-Agent Systems (Preview)

### Parallel Expert Architecture

Poetiq runs **8 experts in parallel**, each with:
- Different random seeds
- Potentially different LLMs (Gemini, GPT, Claude)
- Independent refinement loops

This is a **multi-agent orchestration pattern** where:
1. Agents work independently (no communication during solving)
2. Results are aggregated via voting
3. Diversity is explicitly valued (diversity-first ranking)

### Voting & Consensus

```python
# Poetiq's voting mechanism
1. Group solutions by identical test outputs
2. Count "votes" for each unique answer
3. Prioritize diversity: one representative per output group
4. Rank by vote count + soft scores
```

This connects to **ensemble methods** and **Condorcet jury theorem** — multiple independent judges improve accuracy.

---

## Cross-Cutting Concepts

### Intelligence as Process, Not Just Model

| Course Teaching | Poetiq Evidence |
|-----------------|-----------------|
| Agentic > Chained (L1) | Iterative refinement beats single-pass |
| Reflection improves output (L2) | 10 iterations find solutions 1 pass misses |
| Multi-agent beats single agent (L3) | 8 experts with voting outperform monolithic approach |

### Cost Efficiency Through Orchestration

**Course Principle**: Smart tool use and agent design can reduce costs.

**Poetiq Results**:
- Previous SOTA: $77.16/problem
- Poetiq: $30.57/problem
- **60% cost reduction** through orchestration

---

## Discussion Questions

1. **L2 Connection**: How does Poetiq's execution-based feedback compare to human-in-the-loop? What are the tradeoffs?

2. **L3 Preview**: Why might 8 diverse experts with voting beat a single more powerful model? (Hint: Scott Page's Diversity Prediction Theorem)

3. **Architecture Choice**: Poetiq chose code generation over direct answer prediction. How does this enable better reflection? What other domains could use "executable intermediate representations"?

4. **Generalization**: Could you apply Poetiq's pattern to the B2B research agent from L2? What would "execution-based feedback" look like for sales outreach?
