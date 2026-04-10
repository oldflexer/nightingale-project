from src.interfaces import Summarizer
from loguru import logger

class OpenRouterSummarizer(Summarizer):
    def summarize(self, raw_text: str) -> str:
        logger.info("Summarizing via OpenRouter (mock)")
        # Возвращаем первые 500 символов как "выжимку"
        return raw_text[:500] + "... (mock summary)"