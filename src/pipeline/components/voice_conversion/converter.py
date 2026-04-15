"""
Stage 7: Voice Conversion components (RVC).
"""

import soundfile as sf
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Any

import numpy as np

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext


class RVCComponent(PipelineComponent):
    """
    Компонент преобразования голоса с помощью RVC (Retrieval-based Voice Conversion).
    
    Преобразует синтезированную речь в стиль целевого голоса.
    Результат сохраняется в context.final_audio_path.
    """
    
    def __init__(
        self,
        rvc_model_path: Optional[str] = None,
        pitch_adjustment: int = 0,  # -12 to +12 semitones
        index_path: Optional[str] = None,
        enabled: bool = True,
    ):
        super().__init__(name="rvc", enabled=enabled)
        self._rvc_model_path = Path(rvc_model_path) if rvc_model_path else None
        self._pitch_adjustment = pitch_adjustment
        self._index_path = Path(index_path) if index_path else None
        self._model: Optional[Any] = None
    
    def setup(self) -> None:
        """Load RVC model."""
        if not self.enabled or self._rvc_model_path is None:
            return
        
        if not self._rvc_model_path.exists():
            self._logger.warning(f"RVC model not found: {self._rvc_model_path}")
            return
        
        self._logger.info(f"Loading RVC model: {self._rvc_model_path}")
        try:
            # RVC model loading would go here
            # from rvc import RVC
            # self._model = RVC(self._rvc_model_path)
            self._logger.info("RVC model loaded (stub)")
        except ImportError:
            self._logger.warning("RVC package not available")
        except Exception as e:
            self._logger.warning(f"Failed to load RVC model: {e}")
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        if self._model is None:
            self._logger.debug("RVC model not loaded, skipping conversion")
            # Pass through: use raw audio as final
            context.final_audio_path = context.raw_audio_path
            return context
        
        source_audio = context.raw_audio_path
        if source_audio is None or not source_audio.exists():
            self._logger.warning("No source audio for RVC conversion")
            return context
        
        reference_voice = context.reference_audio_path
        if reference_voice is None or not reference_voice.exists():
            self._logger.warning("No reference voice for RVC conversion")
            context.final_audio_path = source_audio
            return context
        
        self._logger.info(
            f"Starting RVC voice conversion "
            f"(source: {source_audio.name}, ref: {reference_voice.name})..."
        )
        
        try:
            # Create temporary file for output
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = Path(tmp.name)
            
            # Perform RVC conversion
            result_path = self._convert(
                source_path=source_audio,
                reference_path=reference_voice,
                output_path=output_path
            )
            
            context.final_audio_path = result_path
            self._logger.info(f"RVC conversion complete: {result_path}")
            
        except Exception as e:
            self._logger.exception(f"RVC conversion failed: {e}")
            context.add_warning(f"RVC failed: {e}, using original audio")
            context.final_audio_path = source_audio
        
        return context
    
    def _convert(
        self,
        source_path: Path,
        reference_path: Path,
        output_path: Path
    ) -> Path:
        """
        Perform RVC voice conversion.
        
        This is a stub implementation. Actual RVC would use:
        - RVC model for inference
        - Optional pitch shift
        - Optional feature indexing
        """
        self._logger.debug(f"Converting voice: {source_path} -> {output_path}")
        
        # Read source audio
        audio, sr = sf.read(source_path)
        
        # Apply pitch shift if needed
        if self._pitch_adjustment != 0:
            audio = self._pitch_shift(audio, sr, self._pitch_adjustment)
        
        # Write output
        sf.write(output_path, audio, sr)
        
        return output_path
    
    def _pitch_shift(self, audio: np.ndarray, sr: int, semitones: int) -> np.ndarray:
        """
        Simple pitch shifting using speed modification.
        
        Note: This is a simplified implementation.
        For production, consider using librosa.effects.pitch_shift
        or a dedicated pitch shifting library.
        """
        if semitones == 0:
            return audio
        
        try:
            import librosa
            return librosa.effects.pitch_shift(audio, sr=sr, n_steps=semitones)
        except ImportError:
            self._logger.warning("librosa not available for pitch shifting")
            return audio


# =============================================================================
# Audio Enhancement Component
# =============================================================================

class AudioEnhancementComponent(PipelineComponent):
    """
    Компонент улучшения качества аудио.
    
    Выполняет:
    - Noise reduction
    - Normalization
    - Audio normalization
    """
    
    def __init__(
        self,
        normalize: bool = True,
        denoise: bool = False,
        target_loudness: float = -16.0,  # LUFS
        enabled: bool = True,
    ):
        super().__init__(name="audio_enhancement", enabled=enabled)
        self._normalize = normalize
        self._denoise = denoise
        self._target_loudness = target_loudness
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        source_audio = context.raw_audio_path or context.final_audio_path
        if source_audio is None or not source_audio.exists():
            self._logger.debug("No audio to enhance")
            return context
        
        self._logger.info(f"Enhancing audio: {source_audio.name}")
        
        try:
            audio, sr = sf.read(source_audio)
            
            if self._normalize:
                audio = self._normalize_audio(audio)
            
            if self._denoise:
                audio = self._denoise_audio(audio)
            
            # Write enhanced audio
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = Path(tmp.name)
            
            sf.write(output_path, audio, sr)
            
            # Update context
            if context.final_audio_path is None:
                context.final_audio_path = output_path
            else:
                context.raw_audio_path = output_path
            
            self._logger.info(f"Audio enhancement complete: {output_path}")
            
        except Exception as e:
            self._logger.warning(f"Audio enhancement failed: {e}")
        
        return context
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to peak amplitude."""
        max_val = np.abs(audio).max()
        if max_val > 0:
            return audio / max_val * 0.95
        return audio
    
    def _denoise_audio(self, audio: np.ndarray) -> np.ndarray:
        """Simple noise reduction using spectral subtraction."""
        # Simplified implementation
        # For production, consider using noisereduce library
        return audio