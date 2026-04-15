"""
Static Parser - returns predefined news.
"""
from datetime import datetime
from loguru import logger

from src.pipeline.interfaces import NewsItem, Parser


class StaticParser(Parser):
    """
    Static parser that returns predefined news.
    
    Useful for testing without network access.
    """

    def __init__(self, source_url: str = ""):
        self.source_url = source_url
    
    def fetch_latest(self) -> list[NewsItem]:
        """Return static news items."""
        logger.info("StaticParser: returning predefined news")
        
        return [
            NewsItem(
                title="Статическая новость 1",
                url="https://example.com/news/1",
                content_text="Это статическое содержание для тестирования пайплайна.",
                date=datetime.now(),
            ),
            NewsItem(
                title="Статическая новость 2",
                url="https://example.com/news/2",
                content_text="Вторая статическая новость для тестирования.",
                date=datetime.now(),
            ),
            NewsItem(
                title="Статическая новость 3",
                url="https://example.com/news/3",
                content_text="Третья статическая новость с более длинным текстом для проверки.",
                date=datetime.now(),
            ),
        ]
