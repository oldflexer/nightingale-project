import torch
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Optional, Callable, List
from loguru import logger
from src.pipeline.interfaces import TTSEngine


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

        # 1. Load Silero TTS model
        logger.info(f"Loading Silero TTS (language={language}, model={model}, voice={voice}, device={self.device})...")
        try:
            from silero import silero_tts
            result = silero_tts(
                language=language,
                speaker=model,
                sample_rate=sample_rate,
                device=self.device
            )
            if len(result) == 2:
                self.tts_model, self.example_text = result
                self.is_legacy = False
                logger.info("Loaded Silero TTS (v5 style, 2 return values)")
                if hasattr(self.tts_model, 'speakers'):
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

        # 2. Load accentor
        if self.use_accent_stress:
            self.accentor = self._load_accentor()
        else:
            self.accentor = None

    def _load_accentor(self) -> Optional[Callable]:
        """Load silero-stress with fallback methods."""
        logger.info("Loading silero-stress for Russian accentuation...")
        try:
            from silero_stress import load_accentor
            accentor = load_accentor()
            if accentor is not None and callable(accentor):
                logger.info("silero-stress loaded (pip package)")
                return accentor
        except Exception as e:
            logger.warning(f"Failed to load silero-stress via pip: {e}")

        try:
            import torch
            torch.set_num_threads(1)
            accentor = torch.hub.load('snakers4/silero-stress', 'silero_stress')
            if accentor is not None and callable(accentor):
                logger.info("silero-stress loaded (torch.hub)")
                return accentor
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
        # Remove '+' stress markers
        # processed = processed.replace('+', '')
        logger.debug(f"Text after preprocessing: {processed[:100]}...")
        return processed

    def _split_text(self, text: str) -> List[str]:
        """
        Split plain text into chunks by sentences, respecting max_chars.
        Returns list of plain text chunks (without SSML tags).
        """
        # Разбиваем на предложения
        sentences = []
        current = ""
        for char in text:
            current += char
            if char in ".!?":
                sentences.append(current.strip())
                current = ""
        if current.strip():
            sentences.append(current.strip())

        # Объединяем предложения в чанки, не превышающие max_chars
        chunks = []
        current_chunk = ""
        overhead = 100  # запас под <speak><prosody rate="slow"><prosody pitch="low">...</prosody></prosody></speak>
        for sent in sentences:
            # Учитываем, что при оборачивании в SSML добавятся теги (примерно 50 символов)
            # Поэтому оставляем запас
            if len(current_chunk) + len(sent) + 1 + overhead <= self.max_chars:
                if current_chunk:
                    current_chunk += " " + sent
                else:
                    current_chunk = sent
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent
        if current_chunk:
            chunks.append(current_chunk)

        # Если не получилось разбить (очень длинное предложение) — режем по словам
        if not chunks:
            words = text.split()
            chunk_size = max(1, (self.max_chars - overhead) // 10)
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                if chunk:
                    chunks.append(chunk)

        logger.info(f"Split text into {len(chunks)} plain chunks (max {self.max_chars} chars)")
        return chunks

    def _wrap_chunk(self, plain_chunk: str) -> str:
        """Wrap plain text chunk into SSML with prosody tags."""
        # Если чанк уже содержит SSML-теги (например, из препроцессинга), не добавляем повторно
        if plain_chunk.strip().startswith('<speak>'):
            return plain_chunk
        escaped = plain_chunk.replace('&', '&amp;') \
                         .replace('<', '&lt;') \
                         .replace('>', '&gt;') \
                         .replace('"', '&quot;') \
                         .replace("'", '&apos;')
        return f'<speak><prosody rate="90%" pitch="-20%">{escaped}</prosody></speak>'

    def synthesize(self, text: str, output_path: Path) -> Path:
        logger.info(f"Synthesizing with Silero TTS, text length {len(text)} chars")
        processed_text = self._preprocess_text(text)

        # Разбиваем на чанки (чистый текст)
        plain_chunks = self._split_text(processed_text)
        if not plain_chunks:
            raise RuntimeError("No text chunks to synthesize")

        audio_segments = []

        for idx, plain_chunk in enumerate(plain_chunks):
            # Оборачиваем чанк в SSML
            ssml_chunk = self._wrap_chunk(plain_chunk)
            # Дополнительная проверка длины (если превышает max_chars + overhead, можно обрезать)
            if len(ssml_chunk) > self.max_chars:
                logger.warning(f"Chunk {idx+1} length {len(ssml_chunk)} exceeds limit, might fail")

            logger.debug(f"Synthesizing chunk {idx+1}/{len(plain_chunks)}, len={len(ssml_chunk)}: {plain_chunk[:50]}...")
            try:
                if not self.is_legacy:
                    audio = self.tts_model.apply_tts(
                        ssml_text=ssml_chunk,          # используем ssml_text
                        speaker=self.voice,
                        sample_rate=self.sample_rate,
                    )
                else:
                    # legacy: не поддерживает SSML, используем обычный текст
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

        # Склейка аудио (без изменений)
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