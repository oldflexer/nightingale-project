"""
Stage 4: Text Processing components (accentuation, yo replacement).
"""
from abc import abstractmethod
from typing import Optional, Callable, Any

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext


# =============================================================================
# Base Classes
# =============================================================================

class TextProcessorComponent(PipelineComponent):
    """
    Базовый класс для компонентов обработки текста.
    
    Обрабатывает текст из source_field и сохраняет в target_field.
    """
    
    def __init__(
        self,
        name: str,
        enabled: bool = True,
        source_field: str = "summarized_text",
        target_field: str = "processed_text",
    ):
        super().__init__(name=name, enabled=enabled)
        self._source_field = source_field
        self._target_field = target_field
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        source_text = getattr(context, self._source_field, "")
        if not source_text:
            self._logger.debug(f"Source field '{self._source_field}' is empty, skipping")
            return context
        
        try:
            processed = self._process_text(source_text)
            setattr(context, self._target_field, processed)
            self._logger.info(
                f"Text processed: {len(source_text)} -> {len(processed)} chars"
            )
            return context
        except Exception as e:
            self._logger.warning(f"Text processing failed: {e}. Using original.")
            setattr(context, self._target_field, source_text)
            context.add_warning(f"{self.name}: processing failed, using original text")
            return context
    
    @abstractmethod
    def _process_text(self, text: str) -> str:
        """Implement actual text processing logic."""
        pass


# =============================================================================
# Accentor Components
# =============================================================================

class SileroAccentorComponent(TextProcessorComponent):
    """
    Компонент расстановки ударений с помощью Silero Stress.
    
    Добавляет маркеры ударений в текст для улучшения произношения.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        remove_markers: bool = True,
        source_field: str = "summarized_text",
        target_field: str = "processed_text",
    ):
        super().__init__(
            name="silero_accentor",
            enabled=enabled,
            source_field=source_field,
            target_field=target_field,
        )
        self._remove_markers = remove_markers
        self._accentor: Optional[Callable] = None
    
    def setup(self) -> None:
        """Load silero-stress model."""
        self._logger.info("Loading silero-stress...")
        self._accentor = self._load_accentor()
        if self._accentor is None:
            self._logger.warning("Accentor not available, will pass through text")
    
    def _load_accentor(self) -> Optional[Callable]:
        """Load silero-stress with fallback methods."""
        # Method 1: pip package
        try:
            from silero_stress import load_accentor
            accentor = load_accentor()
            if callable(accentor):
                self._logger.info("silero-stress loaded (pip package)")
                return accentor
        except ImportError:
            self._logger.debug("silero-stress pip package not found")
        except Exception as e:
            self._logger.warning(f"Failed to load via pip: {e}")
        
        # Method 2: torch.hub
        try:
            import torch
            torch.set_num_threads(1)
            accentor = torch.hub.load(
                'snakers4/silero-stress',
                'silero_stress'
            )
            if callable(accentor):
                self._logger.info("silero-stress loaded (torch.hub)")
                return accentor
        except Exception as e:
            self._logger.warning(f"Failed to load via torch.hub: {e}")
        
        self._logger.error("Could not load silero-stress")
        return None
    
    def _process_text(self, text: str) -> str:
        if self._accentor is None:
            self._logger.debug("Accentor not loaded, returning original text")
            return text
        
        try:
            processed = self._accentor(text)
            
            if self._remove_markers:
                # Remove '+' stress markers
                processed = processed.replace('+', '')
            
            self._logger.debug(f"Accentuation complete: {processed[:100]}...")
            return processed
        except Exception as e:
            self._logger.warning(f"Accentuation failed: {e}")
            return text


class RuaccentComponent(TextProcessorComponent):
    """
    Компонент расстановки ударений с помощью Ruaccent.
    
    Альтернативный компонент для тех, кто использует ruaccent.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        model_size: str = "turbo3.1",
        source_field: str = "summarized_text",
        target_field: str = "processed_text",
    ):
        super().__init__(
            name="ruaccent",
            enabled=enabled,
            source_field=source_field,
            target_field=target_field,
        )
        self._model_size = model_size
        self._accentor: Any = None  # Using Any to avoid type conflicts with RUAccent
    
    def setup(self) -> None:
        """Load ruaccent model."""
        self._logger.info(f"Loading ruaccent ({self._model_size})...")
        try:
            from ruaccent import RUAccent
            self._accentor = RUAccent()
            self._accentor.load()
            self._logger.info("Ruaccent loaded successfully")
        except ImportError:
            self._logger.warning("ruaccent package not found")
        except Exception as e:
            self._logger.warning(f"Failed to load ruaccent: {e}")
    
    def _process_text(self, text: str) -> str:
        if self._accentor is None:
            return text
        
        try:
            # Add accents
            processed = self._accentor.process(text)
            return processed
        except Exception as e:
            self._logger.warning(f"Ruaccent processing failed: {e}")
            return text


# =============================================================================
# Yo-Replacer Components
# =============================================================================

class RuleBasedYoReplacer(TextProcessorComponent):
    """
    Компонент замены 'е' на 'ё' на основе правил.
    
    Использует встроенные словари с 'ё' для замены.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        source_field: str = "summarized_text",
        target_field: str = "processed_text",
    ):
        super().__init__(
            name="yo_replacer_rules",
            enabled=enabled,
            source_field=source_field,
            target_field=target_field,
        )
        self._yo_words = self._load_yo_words()
    
    def _load_yo_words(self) -> set[str]:
        """Load common Russian words with ё."""
        # Базовый набор слов с Ё
        return {
            "ещё", "что", "чтобы", "ничего", "всего", "все",
            "также", "тоже", "теперь", "поэтому", "однако",
            "будут", "будет", "имеет", "всех", "этих", "этого",
            "других", "другого", "другим", "другими", "другое",
            "сначала", "потом", "всегда", "никогда", "иногда",
            "где", "когда", "как", "кто", "что", "чего",
            "человек", "людей", "людям", "людьми", "человеком",
            "вчера", "сегодня", "завтра", "вечер", "утро",
        }
    
    def _process_text(self, text: str) -> str:
        import re
        # Простая замена по словарю
        for word in self._yo_words:
            # Заменяем 'е' на 'ё' только для точных совпадений слов
            pattern = re.compile(r'\b' + re.escape(word.replace('ё', 'е')) + r'\b', re.IGNORECASE)
            text = pattern.sub(word, text)
        return text


class LLMYoReplacer(TextProcessorComponent):
    """
    Компонент замены 'е' на 'ё' с помощью LLM.
    
    Использует языковую модель для более точной замены.
    """
    
    SYSTEM_PROMPT = """
    Ты — русский язык. Твоя задача — заменить букву 'е' на 'ё' в словах, где это необходимо.
    
    Правила:
    1. Заменяй 'е' на 'ё' только в случаях, когда это необходимо по правилам русского языка
    2. Не меняй слова, где 'е' не читается как 'ё'
    3. Возвращай ТОЛЬКО исправленный текст, без пояснений
    4. Сохраняй оригинальный регистр букв
    
    Примеры:
    - "все" -> "всё" (если в контексте)
    - "что" -> "что" (не меняется)
    """
    
    def __init__(
        self,
        llm_client,  # Any object with .generate(prompt) -> str
        enabled: bool = True,
        batch_size: int = 500,
        source_field: str = "summarized_text",
        target_field: str = "processed_text",
    ):
        super().__init__(
            name="llm_yo_replacer",
            enabled=enabled,
            source_field=source_field,
            target_field=target_field,
        )
        self._llm = llm_client
        self._batch_size = batch_size
    
    def _process_text(self, text: str) -> str:
        if not self._llm:
            self._logger.warning("LLM client not set, skipping")
            return text
        
        # Разбиваем на части для обработки
        parts = []
        for i in range(0, len(text), self._batch_size):
            chunk = text[i:i + self._batch_size]
            
            try:
                response = self._llm.generate(
                    prompt=f"{self.SYSTEM_PROMPT}\n\nТекст:\n{chunk}"
                )
                parts.append(response.strip())
            except Exception as e:
                self._logger.warning(f"LLM call failed for chunk: {e}")
                parts.append(chunk)
        
        return " ".join(parts)


# =============================================================================
# Composite Text Processing
# =============================================================================

class CompositeTextProcessor(PipelineComponent):
    """
    Композитный процессор текста — объединяет несколько обработчиков.
    
    Позволяет применить несколько операций последовательно:
    1. Accentor
    2. Yo-Replacer
    """
    
    def __init__(
        self,
        processors: list[TextProcessorComponent],
        enabled: bool = True,
    ):
        super().__init__(name="text_processor", enabled=enabled)
        self._processors = processors
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        self._logger.info(
            f"Running {len(self._processors)} text processors..."
        )
        
        for processor in self._processors:
            if processor.enabled:
                self._logger.debug(f"Running processor: {processor.name}")
                context = processor.process(context)
        
        return context
