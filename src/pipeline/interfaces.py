"""Pipeline interfaces and data models.

This module defines contracts for pipeline components:
- Core interfaces: Parser, Summarizer, TTSEngine, Publisher
- Pipeline interfaces: TextAggregator, TextProcessor, VoiceExtractor, VoiceConverter
- Data models: NewsItem
- ComponentStatus enum
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Self


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class NewsItem:
    """Model for a single news item."""
    title: str
    url: str
    content_text: str
    date: datetime | None = None


# =============================================================================
# Core Interfaces
# =============================================================================

class Parser(ABC):
    """Interface for news parsers."""
    
    @abstractmethod
    def fetch_latest(self) -> list[NewsItem]:
        """Return list of latest news items."""
        ...


class Summarizer(ABC):
    """Interface for text summarizers."""
    
    @abstractmethod
    def summarize(self, raw_text: str) -> str:
        """Return summarized text."""
        ...


class TTSEngine(ABC):
    """Interface for Text-to-Speech engines."""
    
    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> Path:
        """Convert text to audio, save to output_path, return the path."""
        ...


class Publisher(ABC):
    """Interface for audio publishers."""
    
    @abstractmethod
    def publish(self, audio_path: Path, caption: str | None = None) -> bool:
        """Publish audio file, return success status."""
        ...


# =============================================================================
# Pipeline-Specific Interfaces
# =============================================================================

class TextAggregator(ABC):
    """Interface for text aggregation."""
    
    @abstractmethod
    def aggregate(self, news_items: list[Any]) -> str:
        """Aggregate news items into single text."""
        ...


class TextProcessor(ABC):
    """Interface for text processing (accentuation, yo replacement)."""
    
    @abstractmethod
    def process(self, text: str) -> str:
        """Process text and return modified text."""
        ...


class VoiceExtractor(ABC):
    """Interface for voice/audio extraction from reference."""
    
    @abstractmethod
    def extract(self, audio_path: Path) -> tuple[Path, str]:
        """Extract voice from audio file.
        
        Returns:
            Tuple of (processed_audio_path, transcript)
        """
        ...


class VoiceConverter(ABC):
    """Interface for voice conversion (RVC, etc.)."""
    
    @abstractmethod
    def convert(
        self,
        source_path: Path,
        reference_path: Path,
        output_path: Path,
    ) -> Path:
        """Convert voice from source to reference voice style."""
        ...


# =============================================================================
# Component Status
# =============================================================================

class ComponentStatus(Enum):
    """Status of component execution."""
    SKIPPED = auto()
    SUCCESS = auto()
    FAILED = auto()
    WARNING = auto()
