"""
Stage 6: TTS Synthesis components.
"""
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext
from src.interfaces import TTSEngine


class TTSComponent(PipelineComponent):
    """
    Компонент синтеза речи (TTS).
    
    Использует TTSEngine для преобразования текста в аудио.
    Результат сохраняется в context.raw_audio_path.
    """
    
    def __init__(
        self,
        tts_engine: TTSEngine,
        enabled: bool = True,
        use_reference: bool = True,
    ):
        super().__init__(name="tts", enabled=enabled)
        self._tts = tts_engine
        self._use_reference = use_reference
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        text = context.text_for_synthesis
        if not text:
            self._logger.error("No text available for synthesis")
            context.add_error("TTS: no text to synthesize")
            return context
        
        self._logger.info(f"Starting TTS synthesis ({len(text)} chars)...")
        
        try:
            # Create temporary file for output
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = Path(tmp.name)
            
            # Synthesize
            result_path = self._tts.synthesize(text, output_path)
            
            context.raw_audio_path = result_path
            self._logger.info(f"TTS synthesis complete: {result_path}")
            
        except Exception as e:
            self._logger.exception(f"TTS synthesis failed: {e}")
            context.add_error(f"TTS failed: {e}")
        
        return context


class TTSWithVoiceCloneComponent(TTSComponent):
    """
    TTS компонент с поддержкой клонирования голоса.
    
    Использует референсное аудио и транскрипт для клонирования голоса.
    """
    
    def __init__(
        self,
        tts_engine: TTSEngine,
        enabled: bool = True,
    ):
        super().__init__(
            tts_engine=tts_engine,
            enabled=enabled,
            use_reference=True
        )
        self._name = "tts_voice_clone"
    
    @property
    def name(self) -> str:
        return "tts_voice_clone"
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        text = context.text_for_synthesis
        if not text:
            self._logger.error("No text available for synthesis")
            context.add_error("TTS: no text to synthesize")
            return context
        
        reference_audio = context.reference_audio_path
        reference_text = context.reference_transcript
        
        if reference_audio and reference_audio.exists():
            self._logger.info(
                f"Starting TTS with voice cloning "
                f"(text: {len(text)} chars, ref: {reference_audio.name})..."
            )
        else:
            self._logger.info(
                f"Starting TTS without voice cloning "
                f"(text: {len(text)} chars)..."
            )
        
        try:
            # Create temporary file for output
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = Path(tmp.name)
            
            # For F5-TTS style engines that support voice cloning
            if hasattr(self._tts, 'synthesize_with_reference'):
                result_path = self._tts.synthesize_with_reference(
                    text=text,
                    reference_audio=reference_audio,
                    reference_text=reference_text,
                    output_path=output_path
                )
            elif hasattr(self._tts, 'infer'):
                # F5-TTS style
                result_path = self._synthesize_f5_style(
                    text=text,
                    reference_audio=reference_audio,
                    reference_text=reference_text,
                    output_path=output_path
                )
            else:
                # Standard TTS without cloning
                result_path = self._tts.synthesize(text, output_path)
            
            context.raw_audio_path = result_path
            self._logger.info(f"TTS synthesis complete: {result_path}")
            
        except Exception as e:
            self._logger.exception(f"TTS synthesis failed: {e}")
            context.add_error(f"TTS failed: {e}")
        
        return context
    
    def _synthesize_f5_style(
        self,
        text: str,
        reference_audio: Optional[Path],
        reference_text: str,
        output_path: Path
    ) -> Path:
        """
        Synthesize using F5-TTS style API.
        
        This handles the specific requirements of F5-TTS:
        - Reference audio and text
        - Text chunking
        - Sequential synthesis
        """
        import numpy as np
        import soundfile as sf
        
        # Chunk text
        chunks = self._split_text(text, max_chars=250)
        self._logger.info(f"Split text into {len(chunks)} chunks")
        
        audio_segments = []
        sample_rate = None
        
        for idx, chunk in enumerate(chunks):
            self._logger.debug(f"Synthesizing chunk {idx+1}/{len(chunks)}...")
            
            if reference_audio:
                wav, sr, _ = self._tts.infer(
                    gen_text=chunk,
                    ref_file=str(reference_audio),
                    ref_text=reference_text or "",
                    remove_silence=True,
                    nfe_step=8,
                    cfg_strength=1,
                    speed=1.0,
                )
            else:
                wav, sr, _ = self._tts.infer(
                    gen_text=chunk,
                    ref_file="",
                    ref_text="",
                    remove_silence=True,
                )
            
            if sample_rate is None:
                sample_rate = sr
            audio_segments.append(wav)
        
        # Concatenate with silence
        silence_duration = int(0.2 * sample_rate)
        silence = np.zeros(silence_duration, dtype=audio_segments[0].dtype)
        
        final_audio = []
        for i, seg in enumerate(audio_segments):
            if i > 0:
                final_audio.extend(silence)
            final_audio.extend(seg)
        
        sf.write(output_path, final_audio, sample_rate)
        return output_path
    
    def _split_text(self, text: str, max_chars: int = 250) -> list[str]:
        """Split text into sentences, respecting max_chars."""
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in ".!?":
                sentences.append(current.strip())
                current = ""
        if current.strip():
            sentences.append(current.strip())
        
        # Combine into chunks
        chunks = []
        current_chunk = ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) + 1 <= max_chars:
                current_chunk = (current_chunk + " " + sent).strip() if current_chunk else sent
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Fallback for very long sentences
        if not chunks:
            words = text.split()
            for i in range(0, len(words), max_chars // 10):
                chunk = " ".join(words[i:i + max_chars // 10])
                if chunk:
                    chunks.append(chunk)
        
        return chunks
