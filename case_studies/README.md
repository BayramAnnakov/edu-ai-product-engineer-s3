# Case Studies

Real-world examples of AI agent patterns in production systems. Each case study connects course concepts to cutting-edge implementations.

## Available Case Studies

| Case Study | Key Patterns | Related Lessons |
|------------|--------------|-----------------|
| [Poetiq ARC-AGI-2 SOTA](./poetiq-arc-agi-2/) | Reflection Pattern, Multi-Model Ensemble | Lesson 2, Lesson 3 |

---

## Poetiq ARC-AGI-2: Breaking the 50% Barrier

**What**: Poetiq achieved 54% accuracy on ARC-AGI-2, becoming the first to break the 50% barrier while spending half the cost of previous SOTA.

**Why it matters**: Demonstrates that intelligent orchestration of existing models beats scaling a single model — validating core course concepts.

### Course Connections

| Course Concept | Poetiq Implementation |
|----------------|----------------------|
| **Reflection Pattern** (L2) | Iterative code generation with execution-based feedback |
| **External Feedback** (L2) | Ground-truth from actual code execution, not LLM self-critique |
| **Multi-Agent Systems** (L3) | 8 parallel experts with voting-based consensus |
| **Tool Use** (L1-L2) | Code as tool output, sandbox as execution environment |

### Key Insight

> "The future of AI capability may be less about training larger models and more about intelligent orchestration of diverse reasoning processes."

[Read the full analysis →](./poetiq-arc-agi-2/)

---

## Contributing Case Studies

Have a production AI system that demonstrates course patterns? Case studies should include:

1. **Technical Architecture** — How the system works
2. **Course Connections** — Which patterns from lessons apply
3. **Results & Evidence** — Quantitative outcomes
4. **Key Takeaways** — Lessons for practitioners

Open a PR or discuss in class!
