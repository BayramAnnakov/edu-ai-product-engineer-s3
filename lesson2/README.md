# Lesson 2: Building Reliable Agents

## Overview

This lesson evolves from Workshop 1's agentic workflow to demonstrate:

1. **Improved Tool Docstrings** - Docstrings as user manuals for Claude
2. **External Feedback** - Breaking the prompt engineering plateau
3. **Reflection Pattern** - V1 -> Feedback -> V2 structured improvement
4. **Structured Outputs** - Get validated JSON instead of free-text responses

## Key Concept: The Reflection Pattern

```
Turn 1: Generate V1 Research (initial)
         |
         v
Turn 2: Collect External Feedback (human review)
         |
         v
Turn 3: Reflect and Generate V2 (improved)
```

**Why this matters:** External feedback provides signals that the LLM cannot generate through reasoning alone. Human judgment catches errors, adds context, and identifies missing information that breaks the "prompt engineering plateau."

## Files

```
lesson2/
├── research_agent_v2.py      # Main agent with reflection pattern
├── agent_raw_api.py          # Raw API implementation (under the hood)
├── agent_with_sdk.py         # SDK implementation
├── compare_approaches.py     # Comparison script for demo
├── tools/
│   ├── linkedin.py           # Improved LinkedIn tool with quality analysis
│   └── human_feedback.py     # Human-in-the-loop feedback tool
├── prompts/
│   └── reflection.py         # Reflection prompt templates
├── utils/
│   └── observability.py      # Laminar integration
├── demo_data.py              # Demo prospects data
├── requirements.txt          # Dependencies
└── .env.example              # Environment variables template
```

## Setup

### 1. Environment Setup

If you completed Lesson 1, your environment is already set up. Otherwise:

```bash
cd lesson2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Keys

Copy the environment template and add your keys:

```bash
cp .env.example .env
```

Edit `.env` with:
- `ANTHROPIC_API_KEY` - From [console.anthropic.com](https://console.anthropic.com)
- `ENRICHLAYER_API_KEY` - From [enrichlayer.com](https://enrichlayer.com) (free tier available)

## Running the Demo

```bash
python research_agent_v2.py
```

### What to Expect

1. **Turn 1 - V1 Research**: The agent fetches LinkedIn data and generates initial research
2. **Turn 2 - Human Review**: You'll be prompted to review and provide feedback
3. **Turn 3 - V2 Research**: The agent reflects on feedback and generates improved research

### During Human Review

When prompted for feedback, try providing specific input:

```
Rating (1-5, or 'skip' for auto-approve): 3
What could be improved? Add more specific pain points for their industry
What's missing? No mention of recent company news or market position
Any corrections needed? none
```

Or type `skip` for quick demos without detailed feedback.

## Key Teaching Points

### 1. Docstrings as User Manuals

Compare the improved docstring in `tools/linkedin.py`:

```python
@tool(
    "fetch_linkedin_profile",
    """Fetch professional background data from a LinkedIn profile URL.

    USE WHEN: You need to research a person's professional background...

    RETURNS ON SUCCESS:
    - first_name, last_name: Person's name
    - profile_quality: Assessment of data completeness

    RETURNS ON ERROR:
    - error message if: URL invalid, profile not found, API timeout
    ...
    """
)
```

This structured format helps Claude decide **when** and **how** to use tools effectively.

### 2. External Feedback Sources

This lesson demonstrates two forms of external feedback:

1. **Data Quality Signals** (from EnrichLayer)
   - Completeness score
   - Missing fields
   - Quality assessment

2. **Human-in-the-Loop** (via CLI)
   - Human judgment catches what automated checks miss
   - Provides real-world context
   - Most valuable form of external feedback

### 3. The Reflection Pattern

The pattern transforms generic V1 output into specific, actionable V2 research by:
- Explicitly listing issues from feedback
- Applying quality criteria checklist
- Marking assumptions clearly
- Incorporating human-provided context

## Structured Outputs

Structured outputs allow you to get validated JSON instead of free-text responses. This is essential when you need to:
- Save research to a database or CRM
- Pass results to another agent or system
- Ensure consistent, parseable output format

### JSON Schema Definition

In `research_agent_v2.py`, we define a schema for research output:

```python
RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "prospect_name": {"type": "string"},
        "company": {"type": "string"},
        "role": {"type": "string"},
        "pain_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "talking_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"]
        }
    },
    "required": ["prospect_name", "pain_points", "talking_points"]
}
```

### Enabling Structured Outputs

To enable structured outputs, add `output_format` to your `ClaudeAgentOptions`:

```python
options = ClaudeAgentOptions(
    mcp_servers={"research": research_server},
    allowed_tools=[...],
    system_prompt=SYSTEM_PROMPT,
    max_turns=15,
    output_format={
        "type": "json_schema",
        "schema": RESEARCH_SCHEMA
    }
)
```

### When to Use Structured Outputs

| Use Case | Structured Output? |
|----------|-------------------|
| Quick research for human review | No - free text is easier to read |
| Saving to database/CRM | Yes - consistent format required |
| Passing to another agent | Yes - reliable parsing |
| Generating reports | Maybe - depends on downstream needs |
| Integration with external APIs | Yes - ensures compatibility |

### Try It Out

Uncomment the `output_format` option in `research_agent_v2.py` (lines 254-258) to see structured outputs in action. The agent will return JSON that matches the schema instead of free-form text.

## V1 vs V2 Comparison

A typical improvement you'll see:

**V1 (Before Feedback):**
> "Jensen Huang is the CEO of NVIDIA. He likely faces challenges with technology strategy and market competition."

**V2 (After Feedback):**
> "Jensen Huang, CEO of NVIDIA, faces specific challenges including AI chip supply constraints, the competitive landscape with AMD and custom silicon, and managing the transition from gaming to data center as the primary revenue driver. [ASSUMPTION: Based on public market analysis]"

## Connection to Workshop 1

| Workshop 1 | Workshop 2 |
|-----------|-----------|
| `@tool` decorator | Comprehensive docstrings |
| Single tool | Multiple tools in one server |
| Single-turn agent | Multi-turn conversation |
| Self-correction via prompt | Structured reflection with criteria |
| No external validation | External feedback (human + data quality) |

## Observability: See How Agents Work Under the Hood

Understanding what happens inside an AI agent is crucial for debugging and learning. This lesson provides multiple approaches to see what's really happening.

### Option 1: Laminar (Recommended - Full Visibility)

Laminar uses a Rust proxy to intercept ALL Claude Agent SDK communications, revealing:
- Full prompts (including system prompts you don't normally see)
- Complete conversation history (often 10-50x more tokens than expected!)
- Tool calls with inputs AND outputs
- Real token counts and costs

#### Setup

1. Sign up at [laminar.run](https://www.laminar.run)
2. Create a project and get your API key
3. Add to your `.env`:
```bash
LAMINAR_API_KEY=your_key_here
```

4. Run any agent:
```bash
python research_agent_v2.py
```

5. View traces at https://www.laminar.run

#### What You'll See

```
research_with_sdk (trace)
├── Duration: 14.58s
├── Input Tokens: 31,762  ← This is the REAL count!
├── Output Tokens: 705
├── Total Cost: $0.066
└── Full conversation timeline with tool calls
```

**Key Insight**: The SDK might report ~700 tokens, but Laminar reveals the true count is often 30,000+ due to conversation history, system prompts, and tool definitions.

### Option 2: Debug Mode (Quick Console Output)

For quick debugging without external services:

```bash
DEBUG_LLM=true python research_agent_v2.py
```

Shows formatted boxes with prompts, tool calls, and responses:

```
╔══════════════════════════════════════════════════════════════════════╗
║ 🔍 DEBUG: PROMPT → Turn 1: V1 Research                               ║
╠══════════════════════════════════════════════════════════════════════╣
║ Research this prospect for B2B sales outreach...                     ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Option 3: Raw API Comparison

To truly understand what the SDK abstracts away, run:

```bash
python compare_approaches.py
```

This runs the same task with:
1. **Raw Anthropic API** - Full visibility, you see everything
2. **SDK + Laminar** - Abstracted but traced

Compare the outputs to understand what the SDK is doing for you.

### Comparison Files

| File | Purpose |
|------|---------|
| `agent_raw_api.py` | Agent using direct Anthropic API (no SDK) |
| `agent_with_sdk.py` | SDK agent implementation |
| `compare_approaches.py` | Runs both and compares metrics |

### Why Observability Matters

1. **Token growth** - Conversation history accumulates each turn (often 10-50x what you expect)
2. **Cost awareness** - See real costs, not partial SDK metrics
3. **Tool execution** - Full input/output for every tool call
4. **Hidden context** - System prompts and tool definitions add thousands of tokens
5. **Debugging** - Understand why the agent made specific decisions

### SDK Architecture

The Claude Agent SDK abstracts away raw API calls (it uses IPC to the Claude Code CLI). Without observability, you're flying blind. With Laminar, you see everything the SDK sends and receives.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'claude_agent_sdk'"
Ensure your virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API Rate Limits
If EnrichLayer returns 429 errors, wait a moment and try again. The free tier has rate limits.

### Empty Profile Data
Some LinkedIn profiles have privacy settings that restrict data access. Try a different prospect from `demo_data.py`.

### Laminar Not Working
If observability doesn't initialize:
1. Check that `LAMINAR_API_KEY` is set in `.env`
2. Ensure you installed the observability dependencies: `pip install 'lmnr[claude-agent-sdk]'`
3. The agent works without Laminar - it's optional

---

## Further Reading

### Case Study: Poetiq ARC-AGI-2 SOTA

See how the Reflection Pattern helped achieve state-of-the-art results on a major AI benchmark:

**[Poetiq ARC-AGI-2 Analysis](../case_studies/poetiq-arc-agi-2/)** — How Poetiq broke the 50% barrier on ARC-AGI-2 using:
- **Grounded Reflection**: Execution-based feedback instead of LLM self-critique
- **Multi-Expert Voting**: 8 parallel agents with diversity-first consensus
- **Cost Efficiency**: 54% accuracy at half the cost of previous SOTA

This case study demonstrates the Reflection Pattern at production scale, validating the core concepts from this lesson.

### Theoretical Foundations

- **Scott Page, *The Model Thinker*** — The mathematical foundation for why diverse ensembles outperform single models
- **[Andrew Ng on Reflection Pattern](https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-2-reflection/)** — Agentic design patterns series
