"""
Stage 2: Aggregation components.
"""
from typing import Optional

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext
from src.pipeline.interfaces import NewsItem


class DefaultAggregator(PipelineComponent):
    r"""
    Standard aggregator - combines news into text.
    
    Format:
        --- Title 1 ---
        News text 1
        
        --- Title 2 ---
        News text 2
        ...
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="aggregator", enabled=enabled)
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        if not self._validate_context(context, ["news_items"]):
            return context
        
        news_items = context.news_items
        if not news_items:
            self._logger.warning("No news items to aggregate")
            context.aggregated_text = ""
            return context
        
        self._logger.info(f"Aggregating {len(news_items)} news items...")
        
        parts = []
        for item in news_items:
            if isinstance(item, NewsItem):
                parts.append(f"--- {item.title} ---\n{item.content_text}")
            else:
                # Fallback for dict-like objects
                title = getattr(item, 'title', 'No title')
                content = getattr(item, 'content_text', str(item))
                parts.append(f"--- {title} ---\n{content}")
        
        context.aggregated_text = "\n\n".join(parts)
        self._logger.info(f"Aggregated text: {len(context.aggregated_text)} chars")
        
        return context


class StructuredAggregator(PipelineComponent):
    r"""
    Structured aggregator - creates more readable text.
    
    Format:
        Today in the news:
        
        First: Title. Text.
        Second: Title. Text.
        And third: Title. Text.
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="structured_aggregator", enabled=enabled)
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        if not self._validate_context(context, ["news_items"]):
            return context
        
        news_items = context.news_items
        if not news_items:
            self._logger.warning("No news items to aggregate")
            context.aggregated_text = ""
            return context
        
        self._logger.info(f"Creating structured aggregation of {len(news_items)} items...")
        
        parts = ["Today in the news:"]
        
        for i, item in enumerate(news_items, 1):
            if isinstance(item, NewsItem):
                title = item.title
                content = item.content_text
            else:
                title = getattr(item, 'title', 'No title')
                content = getattr(item, 'content_text', str(item))
            
            # Format each news item
            formatted = f"{title}. {content}"
            parts.append(formatted)
        
        context.aggregated_text = " ".join(parts)
        self._logger.info(f"Aggregated text: {len(context.aggregated_text)} chars")
        
        return context