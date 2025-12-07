# AI Product Engineer Course - Season 3

A hands-on course for building production-ready AI agents and workflows. Learn to make critical architectural decisions, implement multi-agent systems, and deploy AI products that deliver real business value.

## Course Overview

This course teaches you how to build AI products through 5 progressive workshops, each adding complexity while maintaining real-world applicability. By the end, you'll have built a complete production system from scratch.

### What You'll Build

**AutoReach** - An AI-powered B2B sales pipeline that:
- Researches prospects across multiple data sources
- Generates personalized outreach messages
- Self-corrects when encountering messy data
- Evaluates and optimizes its own performance
- Runs in production with monitoring and observability

### Learning Path

```
Workshop 1 (150 lines)     → Chained vs Agentic Workflows
Workshop 2 (450 lines)     → Tool Mastery & Reflection Pattern
Workshop 3 (900 lines)     → Multi-agent orchestration system
Workshop 4 (1,200 lines)   → Evaluation framework & A/B testing
Workshop 5 (2,500+ lines)  → Multi-modal capabilities (voice, code, UI)
```

## Repository Structure

```
edu-ai-product-engineer-s3/
├── README.md                    (You are here)
├── CONTRIBUTIONS.md             (Homework submission guidelines)
├── LICENSE
├── lesson1/                     (Chained vs Agentic Workflows)
│   ├── README.md               (Lesson overview)
│   ├── SETUP_GUIDE.md          (Step-by-step setup)
│   ├── TROUBLESHOOTING.md      (Common issues)
│   ├── agent_outreach.py       (Agentic workflow implementation)
│   ├── chained_outreach.py     (Chained workflow implementation)
│   ├── test_cases.py           (Test URLs)
│   ├── verify_setup.py         (Setup verification script)
│   ├── n8n.json                (No-code demo workflow)
│   └── requirements.txt
├── lesson2/                     (Tool Mastery & Reflection Pattern)
│   ├── README.md               (Lesson overview)
│   ├── research_agent_v2.py    (Main demo: Reflection pattern)
│   ├── agent_raw_api.py        (Raw API implementation)
│   ├── agent_with_laminar.py   (SDK + observability)
│   ├── compare_approaches.py   (Side-by-side comparison)
│   ├── demo_data.py            (Test data & scenarios)
│   ├── tools/
│   │   ├── linkedin.py         (Enhanced LinkedIn tool)
│   │   └── human_feedback.py   (Human-in-the-loop tool)
│   ├── prompts/
│   │   └── reflection.py       (Prompt templates)
│   ├── utils/
│   │   └── observability.py    (Laminar integration)
│   └── requirements.txt
├── lesson3/                     (Coming soon)
├── lesson4/                     (Coming soon)
└── lesson5/                     (Coming soon)
```

## Prerequisites

### Technical Requirements
- **Python 3.10+** (3.11 recommended)
- **Node.js 18+** (for Claude CLI)
- Basic command line knowledge
- Git installed and configured

### Required Accounts (Free Tiers Available)
1. **Anthropic API** - For Claude models
   - Sign up: https://console.anthropic.com
   - Get API key: https://console.anthropic.com/settings/keys
   - Free tier: $5 credit

2. **EnrichLayer API** - For LinkedIn profile enrichment
   - Sign up: https://enrichlayer.com
   - Get API key: https://enrichlayer.com/dashboard/api-key/
   - Free tier: 100 requests/month

### Recommended Tools
- **n8n** (optional) - For visual workflow demos
  - Install: `npm install -g n8n`
  - Self-hosted automation platform

## Quick Start

### 1. Fork This Repository

Click the "Fork" button at the top right of this page to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/edu-ai-product-engineer-s3.git
cd edu-ai-product-engineer-s3
```

### 3. Start with Lesson 1

```bash
cd lesson1
```

Follow the detailed setup instructions in [lesson1/SETUP_GUIDE.md](lesson1/SETUP_GUIDE.md).

## Homework Submission Process

All homework is submitted via **Pull Requests** to your fork. This mirrors real-world software development workflows and builds your GitHub portfolio.

### Quick Overview

```bash
# 1. Create homework branch
git checkout -b lesson1-homework

# 2. Complete your work
# ... build your implementation ...

# 3. Commit and push
git add .
git commit -m "Lesson 1 Homework: [description]"
git push origin lesson1-homework

# 4. Create PR on GitHub (to your own fork!)
# 5. Share PR link in course chat for review
```

### Detailed Guidelines

For complete submission guidelines, code quality standards, and best practices, see:

**📖 [CONTRIBUTIONS.md](CONTRIBUTIONS.md)** - Your complete guide to:
- Initial setup (fork, clone, upstream)
- Homework workflow (branch → code → commit → PR)
- Code quality standards
- Getting feedback and peer review
- Common pitfalls to avoid
- Bonus challenges
- Portfolio tips

## Course Schedule

| Workshop | Topic | Duration | Homework |
|----------|-------|----------|----------|
| **1** | Chained vs Agentic Workflows | 2 hours | 3-4 hours |
| **2** | Tool Mastery & Reflection Pattern | 2 hours | 4-5 hours |
| **3** | Multi-Agent Systems | 2 hours | 6-8 hours |
| **4** | Eval-Driven Development | 2 hours | 5-6 hours |
| **5** | Multi-Modal Capabilities | 2 hours | 8-10 hours |

**Total**: 10 hours workshops + 26-33 hours homework = **36-43 hours**

## Learning Outcomes

By the end of this course, you will be able to:

### Technical Skills
- ✅ Implement agents using Claude Agent SDK
- ✅ Build custom tools with MCP (Model Context Protocol)
- ✅ Orchestrate multi-agent systems
- ✅ Design evaluation frameworks for LLM outputs
- ✅ Build multi-modal agents (voice, code generation, UI)
- ✅ Integrate voice interfaces with AI agents
- ✅ Create agents that write and execute code
- ✅ Design conversational UI for agentic systems

### Product Skills
- ✅ Make chained vs agentic architecture decisions
- ✅ Calculate ROI for AI automation projects
- ✅ Use LLMs as product managers (A/B test design, iteration)
- ✅ Evaluate AI system performance systematically
- ✅ Plan AI product roadmaps with progressive complexity

### Business Skills
- ✅ Identify workflows that need agents (>20% improvement potential)
- ✅ Estimate costs and savings for AI implementations
- ✅ Communicate technical tradeoffs to stakeholders
- ✅ Build portfolio-worthy projects

## Project Examples from Past Students

After completing this course, students have built:

- **Sales automation**: 10,000 personalized emails/month, 95% deliverability
- **Customer support**: 80% ticket auto-resolution, 5-min avg response time
- **Content generation**: 500 LinkedIn posts/week, 3x engagement vs manual
- **Data enrichment**: 50,000 contacts/month, 90% accuracy, $40K/year savings

## Getting Help

### Resources in Each Lesson
- `README.md` - Overview and quick start
- `SETUP_GUIDE.md` - Detailed setup instructions
- `TROUBLESHOOTING.md` - Common issues and solutions
- `verify_setup.py` - Automated diagnostics

### Community Support
- **Course Chat** - Ask questions, share progress
- **Office Hours** - Weekly live Q&A sessions
- **Peer Review** - Code review on pull requests

### Documentation Links
- [Anthropic Claude Docs](https://docs.anthropic.com)
- [Claude Agent SDK Docs](https://github.com/anthropics/claude-agent-sdk)
- [EnrichLayer API Docs](https://enrichlayer.com/docs)
- [n8n Documentation](https://docs.n8n.io)

## Code of Conduct

This is a collaborative learning environment. We expect:
- Respectful communication
- Constructive feedback on PRs
- Sharing learnings and challenges
- Helping peers when possible

## License

This educational material is licensed under the MIT License. See [LICENSE](LICENSE) for details.

You're free to:
- Use the code for personal and commercial projects
- Modify and build upon the examples
- Share your implementations

We ask that you:
- Provide attribution if sharing course materials
- Don't resell this course content

---

## Ready to Start?

1. ✅ Verify prerequisites installed
2. ✅ Create required API accounts
3. ✅ Fork this repository
4. 🚀 Head to [lesson1/](lesson1/) and begin!

**Questions before starting?** Check the [FAQ](lesson1/TROUBLESHOOTING.md) or reach out in the course chat.

Let's build something amazing! 🚀
