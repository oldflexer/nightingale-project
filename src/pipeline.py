from pathlib import Path
from tempfile import NamedTemporaryFile
from loguru import logger
from src.interfaces import Parser, Summarizer, TTSEngine, Publisher
from src.models import NewsItem

class Pipeline:
    def __init__(
        self,
        parser: Parser,
        summarizer: Summarizer,
        tts: TTSEngine,
        publisher: Publisher,
    ):
        self.parser = parser
        self.summarizer = summarizer
        self.tts = tts
        self.publisher = publisher

    def run(self) -> bool:
        logger.info("Pipeline started")
        try:
            # 1. Парсинг
            news_items = self.parser.fetch_latest()
            if not news_items:
                logger.warning("No news items found")
                return False
            logger.info(f"Found {len(news_items)} news items")

            # 2. Агрегация текста (простая конкатенация)
            raw_text = self._aggregate(news_items)
            logger.debug(f"Aggregated text length: {len(raw_text)} chars")

            # 3. Сжатие LLM
            summary = self.summarizer.summarize(raw_text)
            logger.info(f"Summary length: {len(summary)} chars")

            # 4. Синтез речи
            prefix = 'Внимание! Говорит Москва! Передаем важное правительственное сообщение!... '
            suffix = ' Наше дело правое! Враг будет разбит! Победа будет за нами!...'
            summary = prefix + summary + suffix
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio_path = Path(tmp.name)
            audio_path = self.tts.synthesize(summary, audio_path)

            # 5. Публикация
            success = self.publisher.publish(audio_path, caption=summary[:200])
            if success:
                logger.info("Pipeline finished successfully")
            else:
                logger.error("Pipeline failed during publishing")
            return success

        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            return False

    def _aggregate(self, news_items: list[NewsItem]) -> str:
        parts = []
        for item in news_items:
            parts.append(f"--- {item.title} ---\n{item.content_text}")
        return "\n\n".join(parts)