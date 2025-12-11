# Poetiq ARC-AGI-2 SOTA Analysis

## Executive Summary

Poetiq achieved **54% accuracy** on ARC-AGI-2, becoming the first to break the 50% barrier and significantly outperforming the previous SOTA (Gemini 3 Deep Think at 45%). Remarkably, they did this at **half the cost** ($30.57 per problem vs $77.16).

## Key Innovation: Meta-System Architecture

Poetiq did **not train a new foundation model**. Instead, they built a **Meta-System** that orchestrates existing frontier LLMs to solve problems through iterative code generation and refinement.

### Core Insight
> "The central theme driving AGI progress in 2025 is refinement loops. At its core, a refinement loop iteratively transforms one program into another, where the objective is to incrementally optimize a program towards a goal based on a feedback signal."

---

## Technical Architecture

### 1. Test-Time Compute Reasoning Loop

The system implements a sophisticated refinement loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    REFINEMENT LOOP                          │
├─────────────────────────────────────────────────────────────┤
│  1. Problem Analysis    → LLM analyzes the ARC puzzle       │
│  2. Code Generation     → Generate Python transform()       │
│  3. Sandbox Execution   → Run code against training data    │
│  4. Feedback Analysis   → Compute soft scores, find errors  │
│  5. Iterative Refinement → Feed errors back to LLM          │
│  6. Repeat until success or max iterations                  │
└─────────────────────────────────────────────────────────────┘
```

**Key Parameters:**
- `max_iterations`: 10 refinement attempts per expert
- `max_solutions`: 5 candidate solutions tracked
- `selection_probability`: 1.0 (all previous solutions inform next attempt)
- `temperature`: 1.0 (high randomness for creative problem-solving)

### 2. Multi-Expert Parallel Architecture

```python
# Parallel expert orchestration
async def solve_parallel_coding():
    # Launch multiple experts concurrently
    tasks = [asyncio.create_task(solve_coding(cfg)) for cfg in expert_configs]
    results = await asyncio.gather(*tasks)

    # Voting-based consensus mechanism
    # 1. Separate into "passers" (solved training) and "failures"
    # 2. Group by identical test outputs
    # 3. Diversity-first ranking: one representative per output group
```

**Expert Configurations:**
- **Poetiq-a**: 1 expert
- **Poetiq-b**: 2 experts
- **Poetiq-c**: 8 experts (used for SOTA submission)

### 3. LLM-Agnostic Design

The system works with multiple frontier models:
- Google Gemini (2.5 Pro, 3 Pro Preview)
- OpenAI GPT (5, 5.1)
- Anthropic Claude
- XAI models

**Rapid Adaptation**: Poetiq integrated newly released Gemini 3 and GPT-5.1 models within hours of release.

---

## Code Generation Strategy

### Prompt Engineering (Multi-Shot Hierarchical)

Three solver prompts with escalating sophistication:

| Prompt | Purpose |
|--------|---------|
| SOLVER_PROMPT_1 | Foundational structure, basic methodology |
| SOLVER_PROMPT_2 | Emphasis on iterative refinement, persistence |
| SOLVER_PROMPT_3 | Feedback integration, conciseness |
| FEEDBACK_PROMPT | Incorporates prior solution attempts with scores |

**Key Techniques:**
1. **Role-playing**: "world-class expert," "master Python coder"
2. **Category-Based Taxonomy**: Explicit transformation types guide hypothesis generation
   - Color Transformations
   - Object Isolation
   - Spatial Operations
   - Pattern Generation
3. **Constraint Specification**: Strict function signatures, library restrictions
4. **Failure Analysis**: Dedicated sections on learning from mistakes

### Code Extraction & Execution

```python
# Extract Python from LLM response
code = re.search(r"```python\s*(.*?)```", response, re.DOTALL)

# Execute in sandboxed subprocess
async def run_sandbox(code, inputs):
    # 1.5s timeout, isolated environment
    # Only numpy, scipy, stdlib allowed
    # JSON input/output for safety
```

---

## Feedback & Scoring System

### Soft Scoring Mechanism

```python
def _soft_score(predicted, expected):
    """Compute pixel-accuracy metrics for partial credit"""
    # Returns value between 0-1 based on:
    # - Shape match
    # - Color accuracy per cell
    # - Pattern alignment
```

### Feedback Integration

```python
def _build_feedback(solutions, scores):
    """Generate detailed correctness analysis per example"""
    # For each previous attempt:
    # - Show the code
    # - Show training score achieved
    # - Show specific errors per example
    # - Rank in improving order (worst to best)
```

---

## Voting & Consensus Mechanism

### Diversity-First Ranking

```
Priority Order:
1. Passer diversity → One solution per unique output group
2. Failure group diversity → Ranked by votes + soft scores
3. Remaining passer members → Secondary candidates
4. Remaining failure members → Lowest priority
```

This prevents over-fitting to a single solution pattern while maximizing coverage of different valid approaches.

---

## Resource Management

### Safety & Limits

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `per_iteration_timeout` | 3,600s | Single LLM call limit |
| `sandbox_timeout` | 1.5s | Code execution limit |
| `max_total_timeouts` | 15 | Graceful degradation |
| `per_iteration_retries` | 2 | Error recovery |

### Cost Efficiency

By intelligently orchestrating existing models rather than scaling raw compute:
- **Poetiq**: $30.57 per problem
- **Previous SOTA**: $77.16 per problem
- **Savings**: ~60% cost reduction

---

## Repository Structure

```
poetiq-arc-agi-solver/
├── main.py                    # Entry point, evaluation loop
├── arc_agi/
│   ├── config.py              # Model & hyperparameter settings
│   ├── prompts.py             # 3 solver prompts + feedback prompt
│   ├── solve.py               # Main solver entry
│   ├── solve_coding.py        # Core refinement loop (13.5KB)
│   ├── solve_parallel_coding.py # Multi-expert orchestration
│   ├── llm.py                 # Multi-provider LLM interface
│   ├── sandbox.py             # Isolated code execution
│   ├── scoring.py             # Evaluation metrics
│   └── io.py                  # Data loading
└── data/                      # ARC problem datasets
```

---

## Theoretical Foundations

Poetiq's success can be understood through two established frameworks: the **Reflection Pattern** from AI agent development, and **Many-Model Thinking** from Scott Page's *The Model Thinker*.

### Connection to the Reflection Pattern

The **Reflection pattern** is a core agent design pattern where an AI evaluates and improves its own outputs iteratively. Poetiq implements a **specialized, grounded version** of reflection:

| Reflection Pattern | Poetiq Implementation |
|-------------------|----------------------|
| Agent generates output | LLM generates Python `transform()` function |
| Agent critiques its output | Code executed against training examples |
| Feedback informs next attempt | Error messages + soft scores fed back to LLM |
| Iterate until satisfactory | Up to 10 refinement iterations |

**Critical Distinction — Grounded Reflection**:

Traditional reflection relies on LLM self-critique, which can hallucinate quality. Poetiq's reflection is **grounded in execution**:

```
Traditional Reflection:    LLM → LLM judges itself → may hallucinate quality
Poetiq's Reflection:       LLM → Actual execution → ground truth feedback
```

This "tool-grounded reflection" or "execution-based verification" means the agent cannot fool itself — reality provides the feedback signal. The code either produces correct output or it doesn't.

### Connection to Scott Page's Many-Model Thinking

Scott Page's thesis in *The Model Thinker* is that **diversity of models beats individual model accuracy**. His key principles map directly to Poetiq's architecture:

#### 1. The Diversity Prediction Theorem

> **Collective Error = Average Individual Error − Diversity**

Poetiq's multi-expert system embodies this mathematically:
- 8 experts with different random seeds
- Different LLMs (Gemini, GPT, Claude) have different "cognitive styles"
- **Diversity-first ranking** explicitly prioritizes unique solution approaches before considering duplicates

#### 2. Many Models > One Model

Page argues that multiple models capturing different aspects of reality outperform any single sophisticated model:

```
Single Gemini 3 Deep Think: 45% accuracy, $77/problem
Poetiq's Many-Model System:  54% accuracy, $31/problem
```

The orchestration of diverse models beats a single powerful model — at lower cost.

#### 3. The Condorcet Jury Theorem

Page discusses how voting among independent judges improves accuracy. Poetiq's voting mechanism:
- Groups solutions by identical outputs
- Counts "votes" for each unique answer
- Higher vote count → higher confidence
- Independence maintained through different seeds and models

#### 4. Model Granularity

Page emphasizes using the right model for each aspect of a problem. Poetiq's prompt taxonomy guides different reasoning approaches:
- Color Transformations → one reasoning path
- Spatial Operations → another approach
- Pattern Generation → yet another

### Unified Framework

Here's how these concepts interconnect in Poetiq's system:

```
┌─────────────────────────────────────────────────────────────────┐
│                    POETIQ'S META-SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐   SCOTT PAGE'S MANY-MODEL THINKING        │
│  │   Expert 1      │   • Diverse models (Gemini, GPT, Claude)  │
│  │   Expert 2      │   • Different seeds = different hypotheses│
│  │   Expert N      │   • Voting aggregates wisdom of crowd     │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐   REFLECTION PATTERN                      │
│  │ Generate Code   │   • Self-improvement loop                 │
│  │      ↓          │   • Feedback integration                  │
│  │ Execute & Test  │   • Grounded in actual execution          │
│  │      ↓          │   • Learn from mistakes                   │
│  │ Analyze Errors  │                                           │
│  │      ↓          │                                           │
│  │ Refine & Retry  │                                           │
│  └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Deeper Insight: Intelligence as Process

What Poetiq discovered — and what connects Page's theoretical work to agent design patterns — is that **intelligence emerges from process, not just model capacity**:

| Paradigm | Core Belief | Poetiq's Evidence |
|----------|-------------|-------------------|
| Scale Maximalism | Bigger model = smarter | Orchestrated smaller models beat single large model |
| Many-Model Thinking | Diverse ensemble > single expert | 8 diverse experts with voting outperform monolithic approach |
| Reflection Pattern | Iteration > single pass | 10 refinement loops find solutions that 1 pass misses |

This suggests a synthesis: **The future of AI capability may be less about training larger models and more about intelligent orchestration of diverse reasoning processes** — exactly what both Page's theoretical framework and the Reflection pattern predict.

---

## Key Takeaways

### Why Poetiq Succeeded

1. **Refinement Over Single-Pass**: Instead of asking "what's the answer?", they ask "generate code, run it, what went wrong, try again"

2. **Code as Intermediate Representation**: Solutions are Python functions, enabling precise execution and error feedback

3. **Ensemble Diversity**: Multiple experts with voting prevents over-reliance on single approaches

4. **Model Orchestration > Model Scaling**: Intelligent use of existing models beats throwing more compute at the problem

5. **LLM-Agnostic Design**: Can immediately leverage new model releases

### Implications for AGI Research

This demonstrates that **test-time compute** and **refinement loops** are currently more effective than pre-training scale for reasoning tasks. The approach is:
- More cost-efficient
- More adaptable
- Leverages the latest models immediately

---

## References

### Poetiq Resources
- [Poetiq GitHub Repository](https://github.com/poetiq-ai/poetiq-arc-agi-solver)
- [Poetiq Announcement](https://poetiq.ai/posts/arcagi_announcement/)
- [Poetiq Verified Results](https://poetiq.ai/posts/arcagi_verified/)
- [ARC Prize 2025 Results](https://arcprize.org/blog/arc-prize-2025-results-analysis)

### Theoretical Foundations
- Page, Scott E. *The Model Thinker: What You Need to Know to Make Data Work for You*. Basic Books, 2018.
- [Reflection Pattern in AI Agents](https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-2-reflection/) — Andrew Ng's explanation of the Reflection pattern
