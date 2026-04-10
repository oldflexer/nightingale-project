import torch
from pathlib import Path
from typing import Optional
from loguru import logger
from TTS.api import TTS
from src.interfaces import TTSEngine

class CoquiTTSEngine(TTSEngine):
    def __init__(
        self,
        model_name: str,
        voice_sample: Optional[str] = None,
        language: str = "ru",
        device: str = "auto"
    ):
        self.model_name = model_name
        self.voice_sample = Path(voice_sample) if voice_sample else None
        self.language = language

        # Определяем устройство
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"Loading Coqui TTS model '{model_name}' on {self.device}...")
        self.tts = TTS(model_name).to(self.device)
        logger.info("Coqui TTS model loaded")

        # Проверяем, существует ли файл для клонирования
        if self.voice_sample and not self.voice_sample.exists():
            logger.warning(f"Voice sample file not found: {self.voice_sample}. Will use default voice.")
            self.voice_sample = None

    def synthesize(self, text: str, output_path: Path) -> Path:
        """
        Синтезирует речь из текста и сохраняет в output_path.
        Возвращает тот же путь.
        """
        logger.info(f"Synthesizing speech (Coqui TTS) for text length {len(text)} chars")
        try:
            if self.voice_sample:
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=str(self.voice_sample),
                    language=self.language,
                    file_path=str(output_path)
                )
            else:
                self.tts.tts_to_file(
                    text=text,
                    language=self.language,
                    file_path=str(output_path)
                )
            logger.info(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise