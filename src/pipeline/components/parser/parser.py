"""
Stage 1: Parser Component.
"""
from typing import Optional

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext
from src.pipeline.interfaces import Parser


class ParserComponent(PipelineComponent):
    """
    Компонент парсинга новостей.
    
    Использует Parser (интерфейс) для получения новостей.
    Результат сохраняется в context.news_items.
    """
    
    def __init__(self, parser: Parser, enabled: bool = True):
        super().__init__(name="parser", enabled=enabled)
        self._parser = parser
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        self._logger.info("Fetching latest news...")
        
        try:
            news_items = self._parser.fetch_latest()
            
            if not news_items:
                self._logger.warning("No news items fetched")
                context.add_warning("Parser returned empty list")
            else:
                self._logger.info(f"Fetched {len(news_items)} news items")
            
            context.news_items = news_items
            return context
            
        except Exception as e:
            self._logger.exception(f"Parsing failed: {e}")
            context.add_error(f"Parser failed: {e}")
            return context