from loguru import logger
from src.pipeline.interfaces import Summarizer


class OpenRouterSummarizer(Summarizer):
    def summarize(self, raw_text: str) -> str:
        logger.info("Summarizing via OpenRouter (mock)")
        # Возвращаем первые 500 символов как "выжимку"
        return raw_text[:500] + "... (mock summary)"
