import torch
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Any, Callable, cast
from loguru import logger

from src.pipeline.interfaces import TTSEngine
from src.pipeline.utils import split_text_by_sentences


class SileroTTSEngine(TTSEngine):
    """
    TTS Engine using Silero TTS with support for Russian accentuation.
    Splits long text into chunks and removes stress markers before synthesis.
    """

    def __init__(
        self,
        language: str = "ru",
        model: str = "v5_ru",
        voice: str = "aidar",
        sample_rate: int = 24000,
        device: str = "auto",
        use_accent_stress: bool = False,
        put_yo: bool = False,
        max_chars: int = 500,
        silence_between_chunks: float = 0.2,
    ):
        self.model_name = model
        self.voice = voice
        self.sample_rate = sample_rate
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_accent_stress = use_accent_stress
        self.put_yo = put_yo
        self.max_chars = max_chars
        self.silence_between_chunks = silence_between_chunks
        self.torch_device = torch.device(self.device)
        self.tts_model: Any | None = None
        self.example_text: Any | None = None
        self.symbols: str | None = None
        self.apply_tts_func: Callable[..., Any] | None = None
        self.is_legacy = False
        self.accentor = None

        # 1. Load Silero TTS model
        logger.info(f"Loading Silero TTS (language={language}, model={model}, voice={voice}, device={self.device})...")
        self._load_tts_model(language)

        # 2. Load accentor
        if self.use_accent_stress:
            self.accentor = self._load_accentor()

    def _load_tts_model(self, language: str) -> None:
        """Load Silero TTS model."""
        try:
            from silero import silero_tts
            result = silero_tts(
                language=language,
                speaker=self.model_name,
                sample_rate=self.sample_rate,
                device=self.device
            )
            if len(result) == 2:
                self.tts_model, self.example_text = result
                self.is_legacy = False
                logger.info("Loaded Silero TTS (v5 style, 2 return values)")
                if self.tts_model is not None and hasattr(self.tts_model, 'speakers'):
                    available = self.tts_model.speakers
                    if self.voice not in available:
                        logger.warning(f"Voice '{self.voice}' not in {available}, using '{available[0]}'")
                        self.voice = available[0]
            elif len(result) == 5:
                self.tts_model, self.symbols, self.sample_rate, self.example_text, self.apply_tts_func = result
                self.is_legacy = True
                logger.info(f"Loaded Silero TTS (legacy style, 5 return values), sample_rate={self.sample_rate}")
            else:
                raise ValueError(f"Unexpected return from silero_tts: {len(result)} values")
        except Exception as e:
            logger.error(f"Failed to load Silero TTS: {e}")
            raise

    def _load_accentor(self) -> Callable[[str], str] | None:
        """Load silero-stress with fallback methods."""
        logger.info("Loading silero-stress for Russian accentuation...")
        try:
            from silero_stress import load_accentor
            accentor = load_accentor()
            if accentor is not None and callable(accentor):
                logger.info("silero-stress loaded (pip package)")
                return cast(Callable[[str], str], accentor)
        except Exception as e:
            logger.warning(f"Failed to load silero-stress via pip: {e}")

        try:
            torch.set_num_threads(1)
            accentor = torch.hub.load('snakers4/silero-stress', 'silero_stress')
            if accentor is not None and callable(accentor):
                logger.info("silero-stress loaded (torch.hub)")
                return cast(Callable[[str], str], accentor)
        except Exception as e:
            logger.warning(f"Failed to load silero-stress via torch.hub: {e}")

        logger.warning("silero-stress not available, accent marking disabled")
        return None

    def _preprocess_text(self, text: str) -> str:
        """Apply stress marks then remove '+' markers, optionally replace 'е' with 'ё'."""
        if not self.use_accent_stress or self.accentor is None:
            processed = text
        else:
            try:
                processed = self.accentor(text)
            except Exception as e:
                logger.warning(f"silero-stress failed: {e}")
                processed = text
        
        if self.put_yo:
            processed = processed.replace('+е', 'ё').replace('+Е', 'Ё')
        
        logger.debug(f"Text after preprocessing: {processed[:100]}...")
        return processed

    def _split_text(self, text: str) -> list[str]:
        """Split plain text into chunks by sentences, respecting max_chars."""
        return split_text_by_sentences(
            text,
            max_chars=self.max_chars,
            overhead=100
        )

    def _wrap_chunk(self, plain_chunk: str) -> str:
        """Wrap plain text chunk into SSML with prosody tags."""
        # If chunk already contains SSML tags, skip wrapping
        if plain_chunk.strip().startswith('<speak>'):
            return plain_chunk
        
        escaped = plain_chunk.replace('&', '&amp;')
        escaped = escaped.replace('<', '&lt;')
        escaped = escaped.replace('>', '&gt;')
        escaped = escaped.replace('"', '&quot;')
        escaped = escaped.replace("'", '&apos;')
        
        return f'<speak><prosody rate="90%" pitch="-20%">{escaped}</prosody></speak>'

    def synthesize(self, text: str, output_path: Path) -> Path:
        logger.info(f"Synthesizing with Silero TTS, text length {len(text)} chars")
        processed_text = self._preprocess_text(text)

        # Split into chunks
        plain_chunks = self._split_text(processed_text)
        if not plain_chunks:
            raise RuntimeError("No text chunks to synthesize")

        audio_segments = []

        for idx, plain_chunk in enumerate(plain_chunks):
            ssml_chunk = self._wrap_chunk(plain_chunk)
            
            if len(ssml_chunk) > self.max_chars:
                logger.warning(f"Chunk {idx+1} length exceeds limit, might fail")

            logger.debug(f"Synthesizing chunk {idx+1}/{len(plain_chunks)}: {plain_chunk[:50]}...")
            
            try:
                if not self.is_legacy:
                    if self.tts_model is None:
                        raise RuntimeError("Silero TTS model not loaded")
                    audio = self.tts_model.apply_tts(
                        ssml_text=ssml_chunk,
                        speaker=self.voice,
                        sample_rate=self.sample_rate,
                    )
                else:
                    # Legacy: no SSML support, use plain text
                    if self.apply_tts_func is None:
                        raise RuntimeError("Legacy TTS function not available")
                    if self.tts_model is None:
                        raise RuntimeError("Silero TTS model not loaded")
                    audio = self.apply_tts_func(
                        texts=[plain_chunk],
                        model=self.tts_model,
                        sample_rate=self.sample_rate,
                        symbols=getattr(self, 'symbols', ''),
                        device=self.torch_device
                    )
                    if isinstance(audio, list):
                        audio = audio[0]

                if torch.is_tensor(audio):
                    audio = audio.cpu().numpy()
                if audio.ndim > 1:
                    audio = audio.squeeze()

                audio_segments.append(audio)

            except Exception as e:
                logger.error(f"Chunk {idx+1} synthesis failed: {e}")
                raise RuntimeError(f"Failed to synthesize chunk {idx+1}: {e}")

        # Concatenate audio
        if not audio_segments:
            raise RuntimeError("No audio generated")

        if len(audio_segments) == 1:
            final_audio = audio_segments[0]
        else:
            silence_samples = int(self.silence_between_chunks * self.sample_rate)
            silence = np.zeros(silence_samples, dtype=audio_segments[0].dtype)
            final_audio = []
            for i, seg in enumerate(audio_segments):
                if i > 0:
                    final_audio.extend(silence)
                final_audio.extend(seg)

        sf.write(output_path, final_audio, self.sample_rate)
        logger.info(f"Audio saved to {output_path}")
        return output_path