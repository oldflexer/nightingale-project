"""
Stage 3: Summarization/Compression components.
"""

from loguru import logger

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext
from src.pipeline.interfaces import Summarizer
from src.pipeline.components.summarization.mock_summarizer import MockSummarizer


class LLMSummarizerComponent(PipelineComponent):
    """
    Компонент сжатия текста с помощью LLM.
    
    Использует Summarizer (интерфейс) для генерации краткого содержания.
    Результат сохраняется в context.summarized_text.
    
    При недоступности LLM автоматически переключается на MockSummarizer.
    """
    
    def __init__(
        self,
        summarizer: Summarizer,
        enabled: bool = True,
        prefix: str = "",
        suffix: str = "",
        fallback_to_mock: bool = True,
        mock_max_chars: int = 500,
    ):
        super().__init__(name="summarizer", enabled=enabled)
        self._summarizer = summarizer
        self._prefix = prefix
        self._suffix = suffix
        self._fallback_to_mock = fallback_to_mock
        self._mock_max_chars = mock_max_chars
        self._mock_summarizer: Summarizer | None = None
        self._using_mock = False
    
    def _get_mock_summarizer(self) -> Summarizer:
        """Lazy initialization of mock summarizer."""
        if self._mock_summarizer is None:
            self._mock_summarizer = MockSummarizer(max_chars=self._mock_max_chars)
        return self._mock_summarizer
    
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
        
        # Choose summarizer based on availability
        summarizer = self._summarizer
        if self._using_mock:
            summarizer = self._get_mock_summarizer()
            self._logger.info("Using mock summarizer (fallback mode)")
        
        try:
            summary = summarizer.summarize(raw_text)
            
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
            
            # If we were using mock but LLM is now working, log it
            if self._using_mock:
                self._logger.info("LLM recovered, will try it next time")
                self._using_mock = False
            
            return context
            
        except Exception as e:
            self._logger.exception(f"Summarization failed: {e}")
            context.add_error(f"Summarizer failed: {e}")
            
            # Try mock summarizer as fallback
            if self._fallback_to_mock and not self._using_mock:
                self._logger.warning("Switching to mock summarizer fallback")
                self._using_mock = True
                try:
                    mock_summary = self._get_mock_summarizer().summarize(raw_text)
                    full_text = self._prefix + mock_summary + self._suffix
                    context.summarized_text = full_text
                    context.add_warning("Using mock summarizer due to LLM failure")
                    self._logger.info(f"Mock summary generated: {len(mock_summary)} chars")
                    return context
                except Exception as mock_error:
                    self._logger.error(f"Mock summarizer also failed: {mock_error}")
            
            # Final fallback: use original text
            self._logger.info("Using original text as final fallback")
            context.summarized_text = raw_text
            return context
