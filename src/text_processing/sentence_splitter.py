from src.text_processing import TextSplitter
from typing import List

class SentenceSplitter(TextSplitter):
    def __init__(self, max_chars: int = 500, overhead: int = 50):
        self.max_chars = max_chars
        self.overhead = overhead

    def split(self, text: str) -> List[str]:
        # разбивка по предложениям (аналогично текущей логике)
        ...