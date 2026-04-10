from src.text_processing import Accentor
from loguru import logger

class SileroStressAccentor(Accentor):
    def __init__(self):
        self.accentor = self._load()
    
    def _load(self):
        # загрузка silero-stress (как в _load_accentor)
        ...
    
    def process(self, text: str) -> str:
        if not self.accentor:
            return text
        return self.accentor(text).replace('+', '')   # удаляем маркеры