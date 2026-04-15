"""
Mock TTS Engine - for testing without heavy dependencies.
"""
import numpy as np
import soundfile as sf
from pathlib import Path
from loguru import logger

from src.pipeline.interfaces import TTSEngine


class MockTTSEngine(TTSEngine):
    """
    Mock TTS engine that generates silent or simple audio.
    
    Useful for testing pipeline without installing heavy TTS models.
    """

    def __init__(
        self,
        sample_rate: int = 24000,
        duration_seconds: float = 1.0,
    ):
        self.sample_rate = sample_rate
        self.duration_seconds = duration_seconds
    
    def synthesize(self, text: str, output_path: Path) -> Path:
        """Generate mock audio (silence)."""
        logger.info(f"[MockTTS] Generating {self.duration_seconds}s audio for text ({len(text)} chars)")
        
        # Generate silence
        num_samples = int(self.sample_rate * self.duration_seconds)
        audio = np.zeros(num_samples, dtype=np.float32)
        
        sf.write(output_path, audio, self.sample_rate)
        logger.info(f"[MockTTS] Saved to {output_path}")
        
        return output_path
