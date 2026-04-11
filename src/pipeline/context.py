"""
Pipeline Context - контейнер данных для передачи между стадиями.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from loguru import logger


@dataclass
class PipelineContext:
    """
    Контейнер данных, передаваемый через все стадии pipeline.
    
    Attributes:
        news_items: Список новостных записей после парсинга
        aggregated_text: Агрегированный текст из новостей
        summarized_text: Сжатый/реферированный текст
        processed_text: Обработанный текст (ударения, ёфикация)
        reference_audio_path: Путь к референсному аудио для клонирования
        reference_transcript: Транскрипт референсного аудио
        raw_audio_path: Путь к сырому аудио после TTS
        final_audio_path: Путь к финальному аудио после RVC
        published: Флаг успешной публикации
        publish_error: Сообщение об ошибке публикации
        start_time: Время запуска pipeline
        errors: Список ошибок
        warnings: Список предупреждений
        metadata: Дополнительные данные
    """
    # --- Parsing ---
    news_items: list = field(default_factory=list)
    
    # --- Aggregation ---
    aggregated_text: str = ""
    
    # --- Summarization ---
    summarized_text: str = ""
    
    # --- Text Processing ---
    processed_text: str = ""
    
    # --- Voice Preparation ---
    reference_audio_path: Optional[Path] = None
    reference_transcript: str = ""
    
    # --- TTS ---
    raw_audio_path: Optional[Path] = None
    
    # --- Voice Conversion ---
    final_audio_path: Optional[Path] = None
    
    # --- Publishing ---
    published: bool = False
    publish_error: Optional[str] = None
    
    # --- Metadata ---
    start_time: Optional[datetime] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # --- Text to use for synthesis (computed property) ---
    @property
    def text_for_synthesis(self) -> str:
        """Text that should be used for TTS synthesis."""
        return self.processed_text or self.summarized_text or self.aggregated_text
    
    # --- Audio to publish (computed property) ---
    @property
    def audio_to_publish(self) -> Optional[Path]:
        """Audio path that should be published."""
        return self.final_audio_path or self.raw_audio_path
    
    # --- Caption for publishing ---
    @property
    def caption(self) -> str:
        """Caption for the published audio."""
        text = self.text_for_synthesis
        return text[:200] + "..." if len(text) > 200 else text
    
    # --- Error handling ---
    def add_error(self, message: str) -> None:
        """Добавить ошибку в контекст."""
        self.errors.append(message)
        logger.error(f"[PipelineContext] ERROR: {message}")
    
    def add_warning(self, message: str) -> None:
        """Добавить предупреждение в контекст."""
        self.warnings.append(message)
        logger.warning(f"[PipelineContext] WARNING: {message}")
    
    @property
    def has_errors(self) -> bool:
        """Check if context has errors."""
        return len(self.errors) > 0
    
    @property
    def success(self) -> bool:
        """Check if pipeline succeeded."""
        return self.published and not self.has_errors
    
    def __repr__(self) -> str:
        parts = []
        if self.news_items:
            parts.append(f"news={len(self.news_items)}")
        if self.aggregated_text:
            parts.append(f"agg={len(self.aggregated_text)}ch")
        if self.summarized_text:
            parts.append(f"sum={len(self.summarized_text)}ch")
        if self.processed_text:
            parts.append(f"proc={len(self.processed_text)}ch")
        if self.raw_audio_path:
            parts.append(f"raw_audio={self.raw_audio_path.name}")
        if self.final_audio_path:
            parts.append(f"final_audio={self.final_audio_path.name}")
        parts.append(f"published={self.published}")
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return f"PipelineContext({', '.join(parts)})"
