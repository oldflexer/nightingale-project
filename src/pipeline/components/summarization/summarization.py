"""
Stage 3: Summarization/Compression components.
"""
from typing import Optional
from pathlib import Path

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext
from src.pipeline.interfaces import Summarizer


class LLMSummarizerComponent(PipelineComponent):
    """
    Компонент сжатия текста с помощью LLM.
    
    Использует Summarizer (интерфейс) для генерации краткого содержания.
    Результат сохраняется в context.summarized_text.
    """
    
    def __init__(
        self,
        summarizer: Summarizer,
        enabled: bool = True,
        prefix: str = "",
        suffix: str = "",
    ):
        super().__init__(name="summarizer", enabled=enabled)
        self._summarizer = summarizer
        self._prefix = prefix
        self._suffix = suffix
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        if not self._validate_context(context, ["aggregated_text"]):
            return context
        
        raw_text = context.aggregated_text
        if not raw_text:
            self._logger.warning("No text to summarize")
            context.summarized_text = ""
            return context
        
        self._logger.info(f"Summarizing text ({len(raw_text)} chars)...")
        
        try:
            summary = self._summarizer.summarize(raw_text)
            
            if not summary:
                self._logger.warning("Summarizer returned empty result")
                context.add_warning("Summarizer returned empty text")
                context.summarized_text = raw_text  # Fallback to original
                return context
            
            # Добавляем префикс и суффикс
            full_text = self._prefix + summary + self._suffix
            
            context.summarized_text = full_text
            self._logger.info(f"Summary generated: {len(summary)} chars")
            self._logger.debug(f"Summary preview: {summary[:200]}...")
            
            return context
            
        except Exception as e:
            self._logger.exception(f"Summarization failed: {e}")
            context.add_error(f"Summarizer failed: {e}")
            # Fallback: используем оригинальный текст
            self._logger.info("Using original text as fallback")
            context.summarized_text = raw_text
            return context


class PromptBasedSummarizer(PipelineComponent):
    """
    Компонент для добавления префикса/суффикса к тексту.
    
    Используется для добавления стандартных фраз:
    - "Внимание! Говорит Москва!"
    - "Наше дело правое!"
    """
    
    def __init__(
        self,
        prefix: str = "",
        suffix: str = "",
        enabled: bool = True,
    ):
        super().__init__(name="text_enricher", enabled=enabled)
        self._prefix = prefix
        self._suffix = suffix
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        # Определяем исходный текст
        source_field = "summarized_text" if context.summarized_text else "aggregated_text"
        source_text = getattr(context, source_field, "")
        
        if not source_text:
            self._logger.warning("No text to enrich")
            return context
        
        target_field = "summarized_text" if source_field == "aggregated_text" else "processed_text"
        
        enriched = self._prefix + source_text + self._suffix
        setattr(context, target_field, enriched)
        
        self._logger.info(
            f"Text enriched with prefix/suffix. "
            f"Length: {len(source_text)} -> {len(enriched)} chars"
        )
        
        return context
