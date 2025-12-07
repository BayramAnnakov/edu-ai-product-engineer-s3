# 📘 Homework #1 — Chained vs Agentic Workflows

**Author:** Inara
**Project:** AI Product Engineering — Workflow Assignment
**Topic:** News Homepage Analysis (Real Product Scenario)

---

## 1. Overview

This homework is grounded in a real B2B product scenario:
our team needs to understand what appears on news publisher homepages, how article prominence evolves over time, and which stories should be recommended for editorial products.

To explore how **chained** and **agentic** approaches behave in practice, I implemented two complementary workflows:

1. **Agentic Homepage Audit (Playwright MCP)** — a browser-level agent that navigates a homepage like a real user and generates a structured editorial audit.
2. **Deterministic Homepage Snapshot Pipeline + Agentic Trend Analyzer** — a minimal-cost deterministic HTML snapshot scraper using BeautifulSoup, paired with an agent that reasons over snapshot data to identify important stories.

These workflows illustrate two fundamentally different roles:
**deterministic extraction** vs **agentic reasoning**, and how they interact in a real architecture.

---

## 2. Workflow 1 — Agentic Homepage Audit (Playwright MCP)

### 🎯 Purpose

Analyze a homepage *as a real reader sees it* and produce an editorial audit.

### 🧠 Description

This workflow is a **true agentic browser agent**:

* Uses **Playwright MCP server** for real browser control.
* Navigates to the homepage of a publisher.
* Closes cookie banners, promotional popups, overlays.
* Reads visible article cards and identifies structural blocks.
* Selects **≤20 links** to open based on relevance and ambiguity.
* Reads article content to refine topic, type, locality, and quality.
* Produces a structured markdown report covering:

  * homepage structure
  * topic and content-type balance
  * freshness and recency
  * local vs national relevance
  * duplication and noise
  * actionable editorial recommendations
  * Christmas/holiday-related content (focus topic)

### 💡 Why This Workflow Is Agentic

* Performs multi-step reasoning.
* Chooses *what to click* and *when to stop*.
* Adapts to unpredictable UI conditions.
* Produces **interpretation**, not structured data.

This agent simulates the work of a human homepage editor and shows where agentic workflows deliver unique value.

---

## 3. Workflow 2 — Deterministic Snapshot Scraper + Evening Homepage Analysis Agent

This workflow combines a **deterministic time-series scraper** with an **agentic “Evening Homepage Analysis Agent”** that behaves like an automated editor preparing an evening newsletter.

It is built from two main parts:

1. A **deterministic homepage snapshot scraper** that periodically records what is on the homepage.
2. An **agent** that uses these historical snapshots (via MCP tools), selectively fetches article content, and generates a newsletter-style recommendation report.

### 3.1 Deterministic Homepage Snapshot Scraper (Time-Series Layer)

The snapshot scraper is responsible for collecting structured signals about the homepage over time. It is intentionally simple and fully deterministic:

* It performs a **single raw HTML fetch** for each run (using Firecrawl only as an HTML transport layer).
* All parsing happens locally with **BeautifulSoup**:

  * detects article cards and their links
  * maps them to topic blocks/sections
  * extracts visual signals (position, “Plus”/premium badges, update/live indicators, images, etc.)
* It computes an **importance score** for each article based on these signals.
* It saves each run as a JSON snapshot (time-series data), which can be re-parsed later if the logic improves.

This layer does not do any reasoning. It just produces a clean, reproducible dataset of homepage state over time that the agent can later consume.

---

### 3.2 Evening Homepage Analysis Agent (Trend Analyzer over Snapshots)

On top of the snapshot pipeline, I implemented a second agent: the **Evening Homepage Analysis Agent** (`run_evening_analysis` in the code).
Unlike the Playwright homepage audit agent (Workflow 1), this one **does not start from the live homepage**. Instead, it:

* works over **historical snapshot data** via an MCP tool, and
* focuses on **choosing what should go into an evening newsletter** for a given publisher.

#### Tools and Data Sources

The agent is configured with three MCP tool sets:

1. **`homepage-history` MCP server** (custom):

   * `get_top_articles_for_period(publisher, hours=24, max_articles=50)`
     → returns aggregated data from deterministic snapshots:

     * topic block (`topic_block`)
     * max importance score
     * how often an article appeared in the top positions (`times_in_top10`)
     * first/last seen timestamps
     * flags like “plus”/premium, etc.
   * `save_report`
     → persists the final newsletter report to disk with a date-based filename.

2. **`firecrawl` MCP** (primary content tool):

   * `scrape_url`
     → fetches clean article text/markdown for a given URL.
     This is the **default way** to inspect article content for selected candidates.

3. **`playwright` MCP** (fallback only):

   * browser tools like `browser_navigate`, `browser_get_html`, etc.
   * used only when Firecrawl fails, returns empty content, or when the agent needs to inspect paywalls or dynamic UI.

#### Agent Workflow (what it actually does)

The system prompt in `SYSTEM_PROMPT` defines a strict, step-by-step workflow:

1. **Load 24h article history**

   * Call `get_top_articles_for_period(publisher='<publisher_from_user>', hours=24, max_articles=50)`.
   * This gives the agent a **summarized 24h view** of what stayed on the homepage and how prominent it was.

2. **Analyze prominence and patterns**

   * Look at importance metrics like `max_importance_score`, `times_in_top10`, “plus” (premium) content.
   * Identify which stories dominated the homepage over the last 24 hours.

3. **Cluster by topic**

   * Group articles by `topic_block` (e.g. Politics, Local, Sports, Culture, etc.).
   * Treat each topic cluster as a potential “section” of the evening newsletter.

4. **Select newsletter candidates**

   * For **each topic cluster**, select **multiple** articles (at least 2–3).
   * Ensure a diverse mix of topics across all clusters.
   * Prioritize:

     * high `max_importance_score`
     * high `times_in_top10`
     * good coverage of different themes (not just one topic).

5. **Inspect content selectively**

   * For top candidates, use `firecrawl.scrape_url` to retrieve article content.
   * Use Playwright only if:

     * Firecrawl fails or returns clearly broken/empty content, or
     * there is a paywall or dynamic UI that needs inspection.
   * The agent **does not** scrape everything — it uses content tools selectively to enrich its judgment.

6. **Generate the evening report**
   The agent produces a markdown report with:

   * **24h Summary**

     * What dominated the news cycle?
     * Which topics were most prominent?

   * **Top Stories by Topic**

     * Articles grouped by topic cluster
     * Original titles **as provided by the data**
     * Links in `[Title](url)` format
     * Short content-based notes on each selected story

   * **Local Focus**

     * 2–3 strongly local-interest stories, with links and brief justification.

   * **Recommendations**

     * Why these articles are newsletter-worthy
     * How they reflect editorial priorities and reader relevance.

7. **Save the report**

   * Finally, the agent uses the `save_report` tool from `homepage-history` to persist the generated markdown:

     * `filename="evening_report"`
     * `publisher="<publisher_slug>"`
     * File name pattern: `YYYY-MM-DD_evening_report_publisher.md`.

#### Why this is a distinct agentic workflow (and different from Workflow 1)

* **Different entry point:**

  * Workflow 1 starts from the *live homepage* via a browser.
  * Workflow 2 starts from **historical, structured snapshot data**.

* **Different goal:**

  * Workflow 1: one-time **homepage audit** (“what is on the homepage right now?”).
  * Workflow 2: **24h trend and newsletter planning** (“what mattered enough to go into the evening product?”).

* **Different tool mix:**

  * Workflow 1: primarily Playwright (UI-focused).
  * Workflow 2: custom `homepage-history` + Firecrawl, with Playwright as a rare fallback.

* **Stronger dependence on deterministic pipeline:**

  * Workflow 2 critically depends on the deterministic snapshot scraper.
  * Without the time-series data from that scraper, the agent cannot see trends or persistence.

---

## 4. Findings

### ✔ Deterministic HTML snapshot extraction is extremely cost-efficient

The most stable and cheapest architecture is:

1. **Fetch raw HTML once** using Firecrawl.
2. **Perform 100% of parsing locally** with BeautifulSoup.

This avoids overreliance on external crawlers and keeps all extraction logic fully deterministic and under our control.

### ✔ Deterministic extraction is essential as the foundation

Using an agent for scraping would be:

* expensive,
* unpredictable,
* difficult to debug,
* and unnecessary for high-frequency tasks.

The HTML snapshot + BeautifulSoup pipeline produces:

* predictable output
* stable structure
* consistent time-series data
* reproducible debugging

### ✔ Agentic browser workflows are far more capable than expected

The Playwright MCP agent can:

* navigate real UI environments,
* close dynamic popups,
* interpret layout,
* and generate editorial insights.

This makes it ideal for tasks requiring **judgment**, not just extraction.

### ✔ Hybrid design yields the strongest results

The deterministic scraper handles repetitive, high-frequency extraction.
The agents handle semantic understanding and editorial evaluation.

This mirrors real newsroom workflow separation:
**data collection** vs **editorial judgment**.

### ✔ Tool selection influences architecture

Experiments showed:

* Playwright is powerful but too heavy for frequent scraping.
* Firecrawl-only fetch is cheap and predictable.
* BeautifulSoup provides full transparency and control.

Thus agents should not be used at the scraping layer.

### ✔ Agents add value only when interpretation is required

Agents shine when tasks involve ambiguity, prioritization, and meaning — not HTML parsing.

---

## 5. Lessons Learned & Insights

1. **Interpretation belongs to agents; extraction belongs to deterministic code.**
2. **High-frequency workflows must avoid agentic behavior to ensure cost stability.**
3. **Snapshot-driven analysis is cheaper and more reliable than repeated agentic browsing.**
4. **Strict constraints are mandatory to prevent agents from overscraping.**
5. **Allowing agents to modify scraper code introduces unacceptable system risks.**

---

## 6. Self-Correction: How the Agents Adapt When Things Go Wrong

In this project, “self-correction” is mainly about **how the agents react when the real web doesn’t match their expectations**: pop-ups, paywalls, missing elements, failed clicks, etc.
The interesting part is not perfection, but the way the agents adjust their plan mid-run instead of just giving up or hallucinating.

### 6.1 Handling Popups and Overlays

In the Playwright-based homepage audit, the agent regularly encounters:

* cookie banners
* full-screen newsletter popups
* promotional overlays that block clicks

Typical pattern:

1. The agent tries to click an element on the page and fails.
2. It “notices” that something is blocking the interaction (e.g. a popup with an “Accept” or “Close” button).
3. It explicitly decides to **close the popup first**, then **retries the original action**.

This looks like:

* “I can’t click the article because a cookie banner is covering the content. I’ll accept cookies first and then continue.”
* “There is a newsletter popup. I’ll close it and then proceed with the homepage analysis.”

The important part: the agent is not just blindly calling browser tools; it **reads the state of the page, updates its mental model, and changes the sequence of actions**.

---

### 6.2 Switching Strategies for Blocked or Broken Content

When working with article content, the agents also adjust behavior when their first approach fails:

* If `firecrawl.scrape_url` returns a paywall page, empty content, or obvious garbage, the agent switches to **Playwright** to inspect the page directly.
* If the article still cannot be accessed (hard paywall), the agent **stops trying to force it**, mentions the limitation in the report, and relies on metadata instead of inventing text.

This is a simple but important self-correction pattern:

* First try the cheapest and cleanest tool.
* If the result is unusable, **change the tool and the plan**, not the reality.
* If both approaches fail, **acknowledge the failure and move on**, instead of hallucinating.

---

### 6.3 Recovering from Navigation or Selector Failures

On some homepages, the structure doesn’t match what the agent “expects”:

* links don’t open the way it thought,
* usual sections or labels are missing,
* elements are nested in unexpected containers.

In these cases the agent often:

* falls back to a more generic strategy (e.g. scanning visible headings and cards instead of relying on one specific selector),
* narrows its goal: instead of trying to perfectly map every block, it focuses on identifying enough representative sections to make a useful editorial judgment.

So when one path fails (“this specific block is not where I thought it would be”), the agent **doesn’t stop** — it **switches to a simpler, more robust heuristic** and continues.

---

### 6.4 Knowing When to Stop

Another subtle self-correction behavior is knowing when to stop doing more work:

* The agent is instructed to inspect only a limited number of articles.
* When it already has a **reasonable spread of topics and examples**, it stops opening new links and moves to writing the report.

This is a form of self-correction in resource usage: instead of “I can always open more,” the agent settles on “this is enough to form an opinion” and shifts from **exploration** to **summarization**.


---

## 7. Biggest Risks & Concerns

### Technical

* HTML structure changes can break parsing rules.
* Token cost volatility in agentic workflows.
* Over-scraping when agent instructions are too permissive.
* Vendor dependency (Playwright, Firecrawl).

### Architectural

* Letting agents alter extraction code could destabilize data pipelines.
* Inconsistent reasoning across runs if prompts are not tightly controlled.

### Non-risks in this assignment

Only public content was used; no legal concerns.

---

## 8. Conclusion

These two workflows demonstrate how **deterministic pipelines** and **agentic reasoning** should coexist in real-world AI systems:

* The snapshot scraper provides **stable, cheap, predictable extraction**.
* The agentic workflows provide **semantic understanding and editorial judgment**.

This hybrid architecture matches real production needs and illustrates a thoughtful application of chained and agentic design patterns.
