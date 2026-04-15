"""
Mock Summarizer - returns truncated text.
"""
from loguru import logger

from src.pipeline.interfaces import Summarizer


class MockSummarizer(Summarizer):
    """
    Mock summarizer for testing.
    
    Simply truncates text to max_chars.
    """

    def __init__(self, max_chars: int = 500):
        self.max_chars = max_chars
    
    def summarize(self, raw_text: str) -> str:
        """Mock summarization - truncate text."""
        logger.info(f"[MockSummarizer] Truncating to {self.max_chars} chars")
        
        if len(raw_text) <= self.max_chars:
            return raw_text
        
        # Find a good break point (sentence or space)
        truncated = raw_text[:self.max_chars]
        last_period = truncated.rfind('.')
        last_space = truncated.rfind(' ')
        
        break_point = max(last_period, last_space)
        if break_point > self.max_chars * 0.5:
            return truncated[:break_point + 1]
        
        return truncated + "..."
