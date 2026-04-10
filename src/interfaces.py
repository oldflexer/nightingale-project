from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from src.models import NewsItem

class Parser(ABC):
    @abstractmethod
    def fetch_latest(self) -> List[NewsItem]:
        """Return list of latest news items."""
        pass

class Summarizer(ABC):
    @abstractmethod
    def summarize(self, raw_text: str) -> str:
        """Return summarized text."""
        pass

class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> Path:
        """Convert text to audio, save to output_path, return the path."""
        pass

class Publisher(ABC):
    @abstractmethod
    def publish(self, audio_path: Path, caption: Optional[str] = None) -> bool:
        """Publish audio file, return success status."""
        pass