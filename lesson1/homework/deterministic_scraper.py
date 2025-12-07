"""
Core homepage scraping logic.

This module contains the scraper that extracts article importance data
from news homepages using Firecrawl and BeautifulSoup.
"""

import logging
import re
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# Fallback for FirecrawlClient if not installed in this specific env
from firecrawl import Firecrawl


logger = logging.getLogger(__name__)


class HomepageScraper:
    """
    Scrapes news homepages and extracts article importance data.

    Uses Firecrawl to fetch HTML content and BeautifulSoup to parse and
    extract article metadata, visual signals, and calculate importance scores.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the scraper with Firecrawl client.

        Args:
            api_key: Optional Firecrawl API key.
        """
        self.firecrawl_client = Firecrawl(api_key=api_key)

    async def scrape_homepage(self, homepage_url: str, publisher_name: str = "Unknown") -> list[dict[str, Any]]:
        """
        Scrape a single news homepage and return extracted articles as dicts.

        Args:
            homepage_url: URL of the homepage to scrape
            publisher_name: Name of publisher for logging

        Returns:
            List of article dictionaries with importance scores
        """
        logger.info(f"Scraping {publisher_name} ({homepage_url})...")

        if not self.firecrawl_client:
            logger.error("Firecrawl client not initialized or library missing.")
            return []
        try:
            # Firecrawl Python SDK usually returns a dict with 'content', 'metadata', 'html', etc.
            # scrape_url is blocking in v1, so we run it in executor if we want true async,
            # but for this script straight call is fine.
            scrape_result = self.firecrawl_client.scrape(
                url=homepage_url,
                formats=["html"]
            )
            html_content = scrape_result.html
        except Exception as e:
            logger.error(f"Firecrawl scrape failed: {e}")
            return []

        if not html_content:
            logger.warning(f"No HTML content returned from {homepage_url}")
            return []

        # Extract articles from HTML
        articles_data = self._extract_articles_from_html(html_content, homepage_url)

        if not articles_data:
            logger.warning(f"No articles extracted from {publisher_name}")
            return []

        # Calculate importance scores
        scored_articles = self._calculate_importance_scores(articles_data)

        logger.info(f"Extracted {len(scored_articles)} articles from {publisher_name}")
        return scored_articles

    def _extract_articles_from_html(self, html: str, base_url: str) -> list[dict[str, Any]]:
        """
        Extract ALL articles from HTML, identifying their topic blocks.

        Strategy:
        1. Find all topic blocks (sections with headers like "Politik", "Sport")
        2. Find all article links with headings
        3. Match articles to their topic blocks

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of article dictionaries with extracted metadata
        """
        soup = BeautifulSoup(html, "html.parser")
        articles = []

        # Step 1: Identify topic blocks
        topic_blocks = self._identify_topic_blocks(soup)

        logger.info(f"Found {len(topic_blocks)} topic blocks: " f"{', '.join({b['topic'] for b in topic_blocks})}")

        # Step 2: Find ALL links with headings (h1, h2, h3, h4)
        seen_links = set()
        position = 1

        # Strategy: Look for all <a> tags that contain headings
        for link in soup.find_all("a", href=True):
            heading = link.find(["h1", "h2", "h3", "h4"])
            if not heading:
                continue

            href = link.get("href", "")

            # Filter out non-article links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Make absolute URL
            if href.startswith("/"):
                href = urljoin(base_url, href)

            # Skip duplicates
            if href in seen_links:
                continue
            seen_links.add(href)

            # Extract title
            title = heading.get_text(strip=True)
            if not title or len(title) < 10:  # Skip very short titles
                continue

            # Find which topic block this article belongs to
            topic_block = self._find_topic_block(link, topic_blocks)

            # Get article container (parent element)
            container = link.find_parent(["article", "div", "section"]) or link

            # Extract signals
            text_content = container.get_text(strip=True)
            has_image = container.find("img") is not None
            has_update_badge = bool(re.search(r"(update|live|eilmeldung|breaking|ticker)", text_content, re.I))
            has_plus_badge = bool(re.search(r"(plus|premium|\+|abo)", text_content, re.I))
            heading_level = int(heading.name[1])  # h2 -> 2, h3 -> 3

            # Simulate dimensions based on content and position
            base_width = 300
            base_height = 200

            if has_image:
                base_height += 150

            # First few articles are typically larger (hero articles)
            if position <= 3:
                base_width = 800
                base_height = 400
            elif position <= 10:
                base_width = 400
                base_height = 250

            width = base_width + min(len(text_content) // 10, 200)
            height = base_height
            area = width * height

            # Distance from top (earlier in DOM = closer to top)
            distance_from_top = position * 100

            articles.append(
                {
                    "title": title,
                    "link": href,
                    "topic_block": topic_block,
                    "width": width,
                    "height": height,
                    "area": area,
                    "distance_from_top": distance_from_top,
                    "position": position,
                    "has_image": has_image,
                    "has_update_badge": has_update_badge,
                    "has_plus_badge": has_plus_badge,
                    "heading_level": heading_level,
                }
            )

            position += 1

        logger.info(f"Extracted {len(articles)} total articles")
        return articles

    def _identify_topic_blocks(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """
        Identify topic blocks (sections) on the homepage.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of topic block dictionaries with element and topic name
        """
        topic_blocks = []

        # Common topic keywords (German + English)
        topic_keywords = [
            "politik",
            "sport",
            "wirtschaft",
            "kultur",
            "panorama",
            "wissen",
            "digital",
            "unterhaltung",
            "berlin",
            "regional",
            "meinung",
            "leben",
            "gesundheit",
            "reise",
            "auto",
            "politics",
            "economy",
            "business",
            "culture",
            "entertainment",
            "technology",
            "science",
            "opinion",
            "health",
            "travel",
            "international",
            "deutschland",
            "ausland",
            "inland",
        ]

        # Strategy 1: Find sections with topic indicators in class/id
        for section in soup.find_all(["section", "div"], class_=True):
            classes = " ".join(section.get("class", [])).lower()
            section_id = (section.get("id") or "").lower()

            for keyword in topic_keywords:
                if keyword in classes or keyword in section_id:
                    topic_blocks.append({"element": section, "topic": keyword.title()})
                    break

        # Strategy 2: Find headings that look like section titles
        for heading in soup.find_all(["h2", "h3"], class_=re.compile(r"(section|topic|category)", re.I)):
            heading_text = heading.get_text(strip=True).lower()

            for keyword in topic_keywords:
                if keyword in heading_text:
                    # Find the parent container
                    parent = heading.find_parent(["section", "div"])
                    if parent:
                        topic_blocks.append({"element": parent, "topic": keyword.title()})
                    break

        return topic_blocks

    def _find_topic_block(self, element: Any, topic_blocks: list[dict[str, Any]]) -> str | None:
        """
        Find which topic block an article element belongs to.

        Args:
            element: BeautifulSoup element (article link)
            topic_blocks: List of identified topic blocks

        Returns:
            Topic name if found, None otherwise
        """
        if not topic_blocks:
            return None

        # Walk up the DOM tree from the element
        current = element
        max_depth = 20  # Limit depth to avoid infinite loops

        for _ in range(max_depth):
            if current is None:
                break

            # Check if current element matches any topic block element
            for block in topic_blocks:
                if current == block["element"]:
                    return block["topic"]

            # Move up to parent
            current = getattr(current, "parent", None)

        return None

    def _calculate_importance_scores(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Calculate importance scores using validated algorithm.
        
        Returns:
            Same list with importance_score added to each article
        """
        if not articles:
            return []

        # Find max values for normalization
        max_area = max(article["area"] for article in articles)
        max_distance = max(article["distance_from_top"] for article in articles)

        scored_articles = []
        for article in articles:
            # Normalize values to 0-100 scale
            position_score = ((21 - article["position"]) / 20) * 100
            # Clamp position score
            position_score = max(0, position_score)
            
            area_score = (article["area"] / max_area) * 100 if max_area > 0 else 0
            proximity_score = (
                ((max_distance - article["distance_from_top"]) / max_distance) * 100 if max_distance > 0 else 0
            )

            # Bonus points
            update_badge_bonus = 15 if article["has_update_badge"] else 0
            plus_badge_bonus = 10 if article["has_plus_badge"] else 0
            heading_level_bonus = 10 if article["heading_level"] == 2 else 0

            # Calculate weighted importance score (out of 100)
            importance_score = (
                position_score * 0.30
                + area_score * 0.25
                + proximity_score * 0.20
                + update_badge_bonus * 0.10
                + plus_badge_bonus * 0.08
                + heading_level_bonus * 0.05
            )

            article["importance_score"] = round(importance_score, 1)
            scored_articles.append(article)

        # Sort by importance score (descending)
        scored_articles.sort(key=lambda x: x["importance_score"], reverse=True)

        return scored_articles

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    async def main():
        # Load environment variables from .env file
        load_dotenv()

        parser = argparse.ArgumentParser(description="Scrape homepage and output JSON")
        parser.add_argument("--url", required=True, help="Homepage URL to scrape")
        parser.add_argument("--publisher", default="cli-test", help="Publisher slug")
        parser.add_argument("--api_key", default=None, help="Firecrawl API Key (optional if env var set)")
        parser.add_argument("--save", action="store_true", help="Save snapshot to disk")
        
        args = parser.parse_args()
        
        # Determine API key: CLI arg > Env var
        api_key = args.api_key or os.getenv("FIRECRAWL_API_KEY")
        
        scraper = HomepageScraper(api_key=api_key)
        
        if not scraper.firecrawl_client:
            print("Error: Firecrawl client could not be initialized. Check dependencies.")
            return

        articles = await scraper.scrape_homepage(args.url, args.publisher)
        
        json_output = json.dumps(articles, indent=2, ensure_ascii=False)
        # print(json_output)

        if args.save:
            # Save to file
            base_dir = Path(__file__).parent.resolve()
            snapshot_dir = base_dir / "snapshots" / args.publisher
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now(timezone.utc)
            filename = now.strftime("%Y-%m-%dT%H-%M-%SZ.json")
            filepath = snapshot_dir / filename
            
            with filepath.open("w", encoding="utf-8") as f:
                f.write(json_output)
            
            print(f"Snapshot saved to {filepath}")
        else:
            print(json_output)

    asyncio.run(main())
