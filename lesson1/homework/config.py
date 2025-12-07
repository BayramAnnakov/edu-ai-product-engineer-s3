"""
Configuration for the Article Scraper Agent.

Simple dataclasses for credentials and optional batch config.
"""

from dataclasses import dataclass


@dataclass
class Credentials:
    """Login credentials for sites requiring authentication."""
    username: str
    password: str 

HOMEPAGES = [
    "https://www.kurier.de",
    "https://www.sueddeutsche.de/",
]