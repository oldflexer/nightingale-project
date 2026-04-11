"""
Stage 5: Voice Preparation components (VAD, STT, transcription).
"""
from pathlib import Path
from typing import Optional, Tuple

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext


# =============================================================================
# Voice Loader Component
# =============================================================================

class VoiceLoaderComponent(PipelineComponent):
    """
    Компонент загрузки референсного аудио для клонирования голоса.
    
    Выполняет:
    1. VAD (Voice Activity Detection) — определение речевых участков
    2. Загрузка и подготовка аудио
    
    Результат сохраняется в context.reference_audio_path.
    """
    
    def __init__(
        self,
        voice_sample_path: Optional[str] = None,
        vad_enabled: bool = True,
        enabled: bool = True,
    ):
        super().__init__(name="voice_loader", enabled=enabled)
        self._voice_sample_path = Path(voice_sample_path) if voice_sample_path else None
        self._vad_enabled = vad_enabled
        self._vad_model = None
    
    def setup(self) -> None:
        """Load VAD model if enabled."""
        if self._vad_enabled:
            self._logger.info("Loading Silero VAD model...")
            try:
                import torch
                torch.set_num_threads(1)
                self._vad_model = torch.hub.load(
                    'snakers4/silero-vad',
                    'silero_vad',
                    trust_repo=True
                )
                self._logger.info("Silero VAD loaded successfully")
            except Exception as e:
                self._logger.warning(f"Failed to load VAD: {e}")
                self._vad_enabled = False
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        if self._voice_sample_path is None:
            self._logger.debug("No voice sample path configured, skipping")
            return context
        
        if not self._voice_sample_path.exists():
            self._logger.warning(f"Voice sample not found: {self._voice_sample_path}")
            context.add_warning(f"Voice sample not found: {self._voice_sample_path}")
            return context
        
        self._logger.info(f"Processing voice sample: {self._voice_sample_path}")
        
        try:
            audio_path = self._voice_sample_path
            
            if self._vad_enabled and self._vad_model:
                audio_path = self._apply_vad(audio_path)
            
            context.reference_audio_path = audio_path
            self._logger.info(f"Voice sample prepared: {audio_path}")
            
        except Exception as e:
            self._logger.error(f"Voice preparation failed: {e}")
            context.add_error(f"Voice loader failed: {e}")
        
        return context
    
    def _apply_vad(self, audio_path: Path) -> Path:
        """Apply VAD to extract speech segments."""
        import torch
        import soundfile as sf
        import numpy as np
        
        self._logger.debug("Applying VAD...")
        
        # Load audio
        audio, sr = sf.read(audio_path)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)  # Convert to mono
        
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).float()
        
        # Get speech timestamps
        speech_probs = self._vad_model(audio_tensor, sr)
        
        # For now, return original path
        # Full VAD implementation would extract speech segments
        self._logger.debug(f"VAD processing complete, audio duration: {len(audio)/sr:.1f}s")
        
        return audio_path


# =============================================================================
# STT Transcription Component
# =============================================================================

class STTTranscriberComponent(PipelineComponent):
    """
    Компонент транскрибации референсного аудио.
    
    Использует STT для получения текста из референсного аудио.
    Результат сохраняется в context.reference_transcript.
    """
    
    def __init__(
        self,
        stt_model: Optional[str] = "silero",
        enabled: bool = True,
    ):
        super().__init__(name="stt_transcriber", enabled=enabled)
        self._stt_model_name = stt_model
        self._stt_model = None
    
    def setup(self) -> None:
        """Load STT model."""
        if self._stt_model_name == "silero":
            self._logger.info("Loading Silero STT model...")
            try:
                import torch
                torch.set_num_threads(1)
                self._stt_model = torch.hub.load(
                    'snakers4/silero-models',
                    'silero_stt',
                    language='ru',
                    trust_repo=True
                )
                self._logger.info("Silero STT loaded successfully")
            except Exception as e:
                self._logger.warning(f"Failed to load Silero STT: {e}")
                self._stt_model = None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        audio_path = context.reference_audio_path
        if audio_path is None:
            self._logger.debug("No reference audio path, skipping transcription")
            return context
        
        if not audio_path.exists():
            self._logger.warning(f"Reference audio not found: {audio_path}")
            return context
        
        self._logger.info(f"Transcribing reference audio: {audio_path}")
        
        try:
            transcript = self._transcribe(audio_path)
            context.reference_transcript = transcript
            self._logger.info(f"Transcription complete: {len(transcript)} chars")
            self._logger.debug(f"Transcript: {transcript[:200]}...")
        except Exception as e:
            self._logger.warning(f"Transcription failed: {e}")
            context.add_warning(f"STT transcription failed: {e}")
        
        return context
    
    def _transcribe(self, audio_path: Path) -> str:
        """Transcribe audio file."""
        if self._stt_model is None:
            return ""
        
        import torch
        import soundfile as sf
        
        # Load audio
        audio, sr = sf.read(audio_path)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        
        audio_tensor = torch.from_numpy(audio).float()
        
        # Decode
        return self._stt_model(audio_tensor, sr).item() if hasattr(self._stt_model, '__call__') else ""


# =============================================================================
# Yo-Replacer for Reference
# =============================================================================

class ReferenceYoReplacerComponent(PipelineComponent):
    """
    Компонент замены 'е' на 'ё' в транскрипте референса.
    
    Выполняет то же самое, что YoReplacer, но для reference_transcript.
    """
    
    def __init__(
        self,
        llm_client=None,
        enabled: bool = True,
    ):
        super().__init__(name="ref_yo_replacer", enabled=enabled)
        self._llm = llm_client
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        transcript = context.reference_transcript
        if not transcript:
            self._logger.debug("No reference transcript, skipping")
            return context
        
        self._logger.info("Replacing Е with Ё in reference transcript...")
        
        try:
            # Simple rule-based replacement for now
            # Could use LLM for more accurate replacement
            processed = self._replace_yo(transcript)
            context.reference_transcript = processed
            self._logger.debug(f"Yo replacement done: {processed[:100]}...")
        except Exception as e:
            self._logger.warning(f"Yo replacement failed: {e}")
        
        return context
    
    def _replace_yo(self, text: str) -> str:
        """Simple rule-based yo replacement."""
        # Common words with ё
        yo_map = {
            "еще": "ещё",
            "никогда": "никогда",
            "все": "всё",  # context-dependent
            "имеет": "имеет",
        }
        
        result = text
        for old, new in yo_map.items():
            result = result.replace(old, new)
        
        return result
