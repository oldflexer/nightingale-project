from pathlib import Path

from loguru import logger

from src.config import settings
from src.pipeline import Pipeline

from src.parser.mil_ru import MilRuParser

from src.interfaces import Summarizer
from src.summarizer.ollama import OllamaSummarizer

from src.interfaces import TTSEngine
from src.tts.coqui import CoquiTTSEngine
from src.tts.f5 import F5TTSEngine
from src.tts.silero import SileroTTSEngine

from src.publisher.telegram import TelegramPublisher


def create_tts(settings) -> TTSEngine:
    tts_type = settings.tts_type
    if tts_type == "coqui":
        return CoquiTTSEngine(
            model_name=settings.tts_model_name,
            voice_sample=settings.tts_voice_sample,
            language=settings.tts_language,
            device=settings.tts_device,
        )
    elif tts_type == "f5":
        return F5TTSEngine(
            ckpt_file=settings.f5_model_name,
            vocab_file=settings.f5_vocab,
            voice_sample=settings.f5_voice_sample,
            timeout=settings.f5_timeout,
            max_retries=settings.f5_max_retries,
            retry_delay=settings.f5_retry_delay,
            vocoder_local_path=settings.vocos_path,
            device=settings.f5_device,
            use_accent_stress=settings.f5_use_accent_stress
        )
    elif tts_type == "silero":
        return SileroTTSEngine(
            language=settings.silero_language,
            model=settings.silero_model,
            voice=settings.silero_voice,
            sample_rate=settings.silero_sample_rate,
            device=settings.silero_device,
            use_accent_stress=settings.silero_use_accent_stress,
            put_yo=settings.silero_put_yo,
            max_chars=settings.silero_max_chars,
            silence_between_chunks=settings.silero_silence_between_chunks,
        )
    else:
        raise ValueError(f"Unknown TTS type: {tts_type}")

def create_summarizer(settings):
    summarizer_type = settings.summarizer_type
    if summarizer_type == "ollama":
        return OllamaSummarizer(
            api_url=settings.ollama_api_url,
            model=settings.ollama_model,
            system_prompt=settings.summary_system_prompt,
            timeout=settings.ollama_timeout,
            max_retries=settings.ollama_max_retries,
            retry_delay=settings.ollama_retry_delay,
            temperature=settings.ollama_temperature,
            max_tokens=settings.ollama_max_tokens
        )
    else:
        raise ValueError(f"Unknown summarizer type: {settings.summarizer_type}")
    
def create_parser():
    if settings.parser_type == "mil_ru":
        return MilRuParser(
            use_dynamic=settings.parser_use_dynamic,
            timeout=20
        )
    else:
        raise ValueError(f"Unknown parser type: {settings.parser_type}")

log_file = Path("nightingale.log")
if log_file.exists():
    log_file.unlink()
    logger.info("Old log file removed")

def main():
    logger.add("nightingale.log", level="TRACE")
    logger.info("Starting Nightingale")
    parser = create_parser()
    summarizer = create_summarizer(settings)
    tts = create_tts(settings)
    publisher = TelegramPublisher()     # заглушка

    pipeline = Pipeline(parser, summarizer, tts, publisher)
    success = pipeline.run()
    if not success:
        logger.error("Pipeline finished with errors")
        exit(1)
    exit(0)

if __name__ == "__main__":
    main()