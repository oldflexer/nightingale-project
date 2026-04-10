from abc import ABC, abstractmethod
from typing import List

class TextSplitter(ABC):
    """Разбивает длинный текст на чанки для последовательного синтеза."""
    @abstractmethod
    def split(self, text: str) -> List[str]:
        pass

class Accentor(ABC):
    """Расставляет ударения и заменяет 'е' на 'ё' в русском тексте."""
    @abstractmethod
    def process(self, text: str) -> str:
        pass