"""
RSS Parser - generic RSS feed parser.
"""
from datetime import datetime
from loguru import logger

from src.pipeline.interfaces import NewsItem, Parser


class RssParser(Parser):
    """
    Generic RSS feed parser.
    
    Fetches news from any RSS feed URL.
    """

    def __init__(self, source_url: str = ""):
        self.source_url = source_url
    
    def fetch_latest(self) -> list[NewsItem]:
        """Fetch latest news from RSS feed."""
        logger.warning(f"RssParser: returning mock data for {self.source_url}")
        
        # Mock data for testing
        return [
            NewsItem(
                title="RSS Новость 1",
                url=f"{self.source_url}/news/1",
                content_text="Содержание первой RSS новости.",
                date=datetime.now(),
            ),
        ]
