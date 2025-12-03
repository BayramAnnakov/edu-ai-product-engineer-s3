# Article Scraper Agent

Simple AI agent that scrapes a single article URL using Playwright MCP.
If the article is behind a paywall/login, it handles authentication reactively.

## Quick Start

```python
from homework.article_scraper import scrape_article, Credentials

# Simple scrape (no auth)
result = await scrape_article("https://example.com/article")

# With login credentials
result = await scrape_article(
    "https://example.com/premium-article",
    credentials=Credentials("user@email.com", "password"),
)

print(result.status)       # ok, login_failed, paywall, error
print(result.html_content) # raw HTML
```

## Installation

```bash
# Python deps (already in venv)
source venv/bin/activate

# Playwright MCP server (auto-installed via npx)
# Requires Node.js 18+

# Set API key
export ANTHROPIC_API_KEY="your-key"
```

## API

### `scrape_article(url, credentials?, max_attempts?)`

Scrapes a single article.

**Arguments:**
- `url` (str): Article URL to scrape
- `credentials` (Credentials, optional): Login credentials
- `max_attempts` (int, default=3): Max retry attempts

**Returns:** `ArticleResult`
- `url`: The article URL
- `title`: Page title
- `html_content`: Raw HTML content
- `status`: "ok" | "login_failed" | "paywall" | "error"
- `attempts`: Number of attempts made
- `notes`: Description of actions taken

### `scrape_articles(urls, credentials?, output_csv?)`

Batch scrape multiple articles.

```python
results = await scrape_articles(
    urls=["https://example.com/a1", "https://example.com/a2"],
    credentials=Credentials("user", "pass"),
    output_csv="./output/articles.csv",
)
```

## How It Works

1. **Navigate to article** directly
2. **Check access** - is content visible?
3. **If blocked** (paywall/login):
   - Find "Log In" link
   - Click → go to login page
   - Fill credentials → submit
   - Navigate BACK to article URL
4. **Extract HTML** content
5. **Return result**

## Run Example

```bash
cd lesson1
python -m homework.article_scraper
```
