from loguru import logger
from src.pipeline.interfaces import Summarizer


class OpenRouterSummarizer(Summarizer):
    """OpenRouter-based text summarizer (placeholder implementation)."""

    def summarize(self, raw_text: str) -> str:
        logger.info("Summarizing via OpenRouter (mock)")
        # Return first 500 characters as "summary"
        return raw_text[:500] + "... (mock summary)"
