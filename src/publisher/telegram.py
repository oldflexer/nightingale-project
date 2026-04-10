from pathlib import Path
from typing import Optional
from src.interfaces import Publisher
from loguru import logger

class TelegramPublisher(Publisher):
    def publish(self, audio_path: Path, caption: Optional[str] = None) -> bool:
        logger.info(f"Publishing to Telegram (mock): audio={audio_path}, caption={caption}")
        return True