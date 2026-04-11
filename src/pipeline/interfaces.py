"""
Pipeline interfaces and base classes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic

from loguru import logger


# =============================================================================
# Context Data Classes
# =============================================================================

@dataclass
class PipelineContext:
    """
    Контейнер данных, передаваемый через все стадии pipeline.
    Использует dataclass с дополнительными методами для удобства доступа.
    """
    # Parsing stage
    news_items: list = field(default_factory=list)
    
    # Aggregation stage
    aggregated_text: str = ""
    
    # Summarization stage
    summarized_text: str = ""
    
    # Text processing stage
    processed_text: str = ""
    
    # Voice preparation stage
    reference_audio_path: Optional[Path] = None
    reference_transcript: str = ""
    
    # TTS stage
    raw_audio_path: Optional[Path] = None
    
    # Voice conversion stage
    final_audio_path: Optional[Path] = None
    
    # Publishing stage
    published: bool = False
    publish_error: Optional[str] = None
    
    # Metadata
    start_time: Optional[datetime] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Добавить ошибку в контекст."""
        self.errors.append(message)
        logger.error(f"[PipelineContext] {message}")
    
    def add_warning(self, message: str) -> None:
        """Добавить предупреждение в контекст."""
        self.warnings.append(message)
        logger.warning(f"[PipelineContext] {message}")
    
    @property
    def audio_to_publish(self) -> Optional[Path]:
        """Return the audio path that should be published."""
        return self.final_audio_path or self.raw_audio_path
    
    def __repr__(self) -> str:
        return (
            f"PipelineContext("
            f"news_items={len(self.news_items)}, "
            f"aggregated={len(self.aggregated_text)} chars, "
            f"summarized={len(self.summarized_text)} chars, "
            f"processed={len(self.processed_text)} chars, "
            f"raw_audio={self.raw_audio_path}, "
            f"final_audio={self.final_audio_path}, "
            f"published={self.published})"
        )


# =============================================================================
# Component Interface
# =============================================================================

class PipelineComponent(ABC):
    """
    Базовый интерфейс для всех компонентов pipeline.
    
    Каждый компонент:
    - Имеет уникальное имя для логирования
    - Может быть включен/выключен
    - Может иметь зависимости от других компонентов
    - Может выполнять setup/teardown
    """
    
    def __init__(self, name: str, enabled: bool = True):
        self._name = name
        self._enabled = enabled
        self._logger = logger.bind(component=name)
    
    @property
    def name(self) -> str:
        """Component name for logging."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Whether component is active."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
    
    @property
    def logger(self):
        """Logger bound to component name."""
        return self._logger
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        Обработать контекст и вернуть обновленный контекст.
        
        Args:
            context: Текущий контекст pipeline
            
        Returns:
            Обновленный контекст
        """
        pass
    
    def setup(self) -> None:
        """
        Опциональный метод инициализации.
        Вызывается один раз перед началом pipeline.
        """
        pass
    
    def teardown(self) -> None:
        """
        Опциональный метод очистки.
        Вызывается после завершения pipeline.
        """
        pass


class ComponentStatus(Enum):
    """Статус выполнения компонента."""
    SKIPPED = "skipped"
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"


# =============================================================================
# Stage Interface
# =============================================================================

class Stage(ABC):
    """
    Стадия pipeline - логическая группа компонентов.
    
    Стадия:
    - Имеет имя для логирования
    - Содержит список компонентов
    - Выполняет компоненты последовательно
    - Может иметь условия выполнения
    """
    
    def __init__(self, name: str, enabled: bool = True):
        self._name = name
        self._enabled = enabled
        self._logger = logger.bind(stage=name)
    
    @property
    def name(self) -> str:
        """Stage name for logging."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Whether stage is active."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
    
    @property
    def logger(self):
        """Logger bound to stage name."""
        return self._logger
    
    @property
    def components(self) -> list[PipelineComponent]:
        """List of components in this stage."""
        return []
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Выполнить все включенные компоненты стадии.
        
        Args:
            context: Текущий контекст pipeline
            
        Returns:
            Обновленный контекст
        """
        if not self.enabled:
            self.logger.info("Stage skipped (disabled)")
            return context
        
        self.logger.info(f"Stage started with {len(self.components)} component(s)")
        
        for component in self.components:
            if not component.enabled:
                self.logger.debug(f"Component '{component.name}' skipped (disabled)")
                continue
            
            self.logger.debug(f"Running component '{component.name}'...")
            try:
                context = component.process(context)
                self.logger.debug(f"Component '{component.name}' completed")
            except Exception as e:
                self.logger.exception(f"Component '{component.name}' failed: {e}")
                context.add_error(f"Stage '{self.name}': Component '{component.name}' failed: {e}")
                return context
        
        self.logger.info("Stage completed")
        return context


# =============================================================================
# Original Interfaces (for compatibility)
# =============================================================================

class Parser(ABC):
    """Interface for news parsers (kept for backward compatibility)."""
    
    @abstractmethod
    def fetch_latest(self) -> list:
        """Return list of latest news items."""
        pass


class Summarizer(ABC):
    """Interface for text summarizers (kept for backward compatibility)."""
    
    @abstractmethod
    def summarize(self, raw_text: str) -> str:
        """Return summarized text."""
        pass


class TTSEngine(ABC):
    """Interface for TTS engines (kept for backward compatibility)."""
    
    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> Path:
        """Convert text to audio and return the path."""
        pass


class Publisher(ABC):
    """Interface for publishers (kept for backward compatibility)."""
    
    @abstractmethod
    def publish(self, audio_path: Path, caption: Optional[str] = None) -> bool:
        """Publish audio file, return success status."""
        pass


class TextAggregator(ABC):
    """Interface for text aggregation."""
    
    @abstractmethod
    def aggregate(self, news_items: list) -> str:
        """Aggregate news items into single text."""
        pass


class TextProcessor(ABC):
    """Interface for text processing (accentuation, yo replacement, etc.)."""
    
    @abstractmethod
    def process(self, text: str) -> str:
        """Process text and return modified text."""
        pass


class VoiceExtractor(ABC):
    """Interface for voice/audio extraction from reference."""
    
    @abstractmethod
    def extract(self, audio_path: Path) -> tuple[Path, str]:
        """
        Extract voice from audio file.
        Returns: (processed_audio_path, transcript)
        """
        pass


class VoiceConverter(ABC):
    """Interface for voice conversion (RVC, etc.)."""
    
    @abstractmethod
    def convert(
        self,
        source_path: Path,
        reference_path: Path,
        output_path: Path
    ) -> Path:
        """Convert voice from source to reference voice style."""
        pass