import time
import torch
import soundfile as sf
from pathlib import Path
from typing import Optional, Callable
from loguru import logger
from src.interfaces import TTSEngine


class F5TTSEngine(TTSEngine):
    """
    TTS Engine using F5-TTS with support for voice cloning and Russian accentuation.
    Uses silero-stress for stress marking instead of ruaccent.
    """

    def __init__(
        self,
        ckpt_file: str,
        vocab_file: str,
        voice_sample: Optional[str] = None,
        use_accent_stress: bool = True,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        device: str = "auto",
        vocoder_local_path: Optional[str] = None,
    ):
        # ... (сохранение параметров) ...
        self.ckpt_file = Path(ckpt_file)
        self.vocab_file = Path(vocab_file)
        self.voice_sample = Path(voice_sample) if voice_sample else None
        self.use_accent_stress = use_accent_stress
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.vocos_path = Path(vocoder_local_path) if vocoder_local_path else None

        # 1. Load silero-stress if needed
        if self.use_accent_stress:
            self.accentor = self._load_accentor()

        # 2. Load F5-TTS model
        logger.info(f"Loading F5-TTS from checkpoint '{self.ckpt_file}' on {self.device}...")
        from f5_tts.api import F5TTS
        self.tts = F5TTS(
            ckpt_file=str(self.ckpt_file),
            vocab_file=str(self.vocab_file),
            device=self.device,
            vocoder_local_path=str(self.vocos_path) if self.vocos_path else None
        )
        logger.info("F5-TTS model loaded successfully")

        # 3. Validate voice sample if provided
        if self.voice_sample and not self.voice_sample.exists():
            logger.warning(f"Voice sample file not found: {self.voice_sample}. Voice cloning will be disabled.")
            self.voice_sample = None

    def _load_accentor(self) -> Optional[Callable]:
        """Load silero-stress with fallback methods."""
        logger.info("Initializing silero-stress for Russian accentuation...")

        # Method 1: Try pip package
        try:
            from silero_stress import load_accentor
            accentor = load_accentor()
            if accentor is not None and callable(accentor):
                logger.info("silero-stress loaded successfully (pip package)")
                return accentor
            else:
                logger.warning("load_accentor() returned None or non-callable")
        except ImportError:
            logger.warning("silero-stress pip package not found")
        except Exception as e:
            logger.warning(f"Failed to load silero-stress via pip: {e}")

        # Method 2: Fallback to torch.hub
        try:
            import torch
            torch.set_num_threads(1)
            accentor = torch.hub.load('snakers4/silero-stress', 'silero_stress')
            if accentor is not None and callable(accentor):
                logger.info("silero-stress loaded successfully (torch.hub)")
                return accentor
        except Exception as e:
            logger.warning(f"Failed to load silero-stress via torch.hub: {e}")

        # Method 3: If all fails, disable stress marking
        logger.error("Could not load silero-stress. Disabling stress marking.")
        self.use_accent_stress = False
        return None

    def _preprocess_text(self, text: str) -> str:
        """Apply Russian stress marks using silero-stress if enabled."""
        if not self.use_accent_stress or self.accentor is None:
            return text
        try:
            processed = self.accentor(text)
            logger.debug(f"Text with accents: {processed}")
            return processed
        except Exception as e:
            logger.warning(f"silero-stress failed: {e}. Returning original text.")
            return text

    def _split_text(self, text: str, max_chars: int = 250) -> list[str]:
        """Разбивает текст на части по предложениям, не превышая max_chars."""
        # Разделители предложений: точка, восклицательный, вопросительный знаки
        sentences = []
        current = ""
        for char in text:
            current += char
            if char in ".!?":
                sentences.append(current.strip())
                current = ""
        if current.strip():
            # Если последнее предложение без знака препинания, добавляем его
            sentences.append(current.strip())
        
        # Объединяем короткие предложения в чанки
        chunks = []
        current_chunk = ""
        for sent in sentences:
            if len(current_chunk) + len(sent) + 1 <= max_chars:
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
        
        # Если чанк получился пустым (например, весь текст в одном предложении, но он длинный),
        # то принудительно разбиваем по словам
        if not chunks:
            words = text.split()
            for i in range(0, len(words), max_chars // 10):
                chunk = " ".join(words[i:i+max_chars//10])
                if chunk:
                    chunks.append(chunk)
        
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    def synthesize(self, text: str, output_path: Path) -> Path:
        import numpy as np
        logger.info(f"Synthesizing with F5-TTS, text length {len(text)} chars")
        processed_text = self._preprocess_text(text)

        ref_text = "Внимание! Говорит Москва! Передаем важное правительственное сообщение!"

        if self.voice_sample and ref_text is None:
            logger.debug(f"Using voice sample: {self.voice_sample} for cloning")
            ref_text = ""  # или укажите транскрипцию вручную
        else:
            ref_text = ""

        # Разбиваем текст на маленькие чанки
        chunks = self._split_text(processed_text, max_chars=250)
        logger.info(f"Split into {len(chunks)} chunks for sequential synthesis")

        audio_segments = []
        sample_rate = None

        for idx, chunk in enumerate(chunks):
            logger.debug(f"Synthesizing chunk {idx+1}/{len(chunks)}: {chunk[:50]}...")
            for attempt in range(1, self.max_retries + 1):
                try:
                    if self.voice_sample:
                        wav, sr, _ = self.tts.infer(
                            gen_text=chunk,
                            ref_file=str(self.voice_sample),
                            ref_text=ref_text,
                            remove_silence=True,
                            nfe_step=8,
                            cfg_strength=1,
                            speed=1.0,
                            sway_sampling_coef=-1,
                            fix_duration=None
                        )
                    else:
                        wav, sr, _ = self.tts.infer(
                            gen_text=chunk,
                            ref_file="",
                            ref_text="",
                            remove_silence=True
                        )
                    if sample_rate is None:
                        sample_rate = sr
                    audio_segments.append(wav)
                    break  # успех, выходим из retry-цикла
                except Exception as e:
                    logger.warning(f"Chunk {idx+1} failed (attempt {attempt}): {e}")
                    if attempt == self.max_retries:
                        raise RuntimeError(f"Failed to synthesize chunk {idx+1} after {self.max_retries} attempts: {e}")
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))

        if sample_rate is None:
            raise RuntimeError("No audio segments generated, sample_rate is None")

        # Склеиваем все чанки, добавляя небольшую паузу между ними
        silence_duration = int(0.2 * sample_rate)
        silence = np.zeros(silence_duration, dtype=audio_segments[0].dtype)

        final_audio = []
        for i, seg in enumerate(audio_segments):
            if i > 0:
                final_audio.extend(silence)
            final_audio.extend(seg)

        # Сохраняем результат
        sf.write(output_path, final_audio, sample_rate)
        logger.info(f"Audio saved to {output_path}")
        return output_path