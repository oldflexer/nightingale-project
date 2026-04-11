"""
Nightingale - News to Telegram Audio Pipeline

Main entry point using the new modular pipeline architecture.
"""
from pathlib import Path

from loguru import logger

from src.config import settings
from src.parser.mil_ru import MilRuParser
from src.summarizer.ollama import OllamaSummarizer
from src.tts.silero import SileroTTSEngine
from src.tts.f5 import F5TTSEngine
from src.tts.coqui import CoquiTTSEngine
from src.publisher.telegram import TelegramPublisher


# =============================================================================
# Factory functions for creating components
# =============================================================================
def create_parser():
    """Create parser based on settings."""
    if settings.parser_type == "mil_ru":
        return MilRuParser(
            use_dynamic=settings.parser_use_dynamic,
            timeout=20
        )
    else:
        raise ValueError(f"Unknown parser type: {settings.parser_type}")


def create_summarizer():
    """Create summarizer based on settings."""
    if settings.summarizer_type == "ollama":
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


def create_tts():
    """Create TTS engine based on settings."""
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


def create_publisher():
    """Create publisher based on settings."""
    if settings.publisher_type == "telegram":
        return TelegramPublisher(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id
        )
    else:
        raise ValueError(f"Unknown publisher type: {settings.publisher_type}")


# =============================================================================
# Main function
# =============================================================================
def main():
    # Configure logging
    log_file = Path("nightingale.log")
    if log_file.exists():
        log_file.unlink()

    logger.add("nightingale.log", level="DEBUG", format="{time} | {level} | {name}:{function}:{line} | {message}")
    logger.info("=" * 60)
    logger.info("Starting Nightingale (New Pipeline Architecture)")
    logger.info("=" * 60)

    # Create components
    parser = create_parser()
    summarizer = create_summarizer()
    tts_engine = create_tts()
    publisher = create_publisher()

    # Build pipeline using the builder
    from src.pipeline import PipelineBuilder

    pipeline = (PipelineBuilder()
        .with_parsing(parser)
        .with_aggregation(aggregator_type="default")
        .with_summarization(
            summarizer,
            prefix='Внимание! Говорит Москва! Передаем важное правительственное сообщение!... ',
            suffix=' Наше дело правое! Враг будет разбит! Победа будет за нами!...'
        )
        # Stage 4: Text Processing (optional)
        # Uncomment to enable:
        # .with_text_processing(accentor=True, accentor_type="silero", yo_replacer=False)

        # Stage 5: Voice Preparation (optional)
        # Uncomment to enable voice cloning:
        # .with_voice_preparation(
        #     voice_sample_path=settings.f5_voice_sample,
        #     use_stt=True
        # )

        .with_tts(tts_engine, use_voice_clone=bool(settings.f5_voice_sample))

        # Stage 7: Voice Conversion (optional)
        # Uncomment to enable RVC:
        # .with_voice_conversion(rvc_model_path="models/rvc/model.pth")

        .with_publishing(publisher)
        .build())

    # Print pipeline summary
    logger.info("\n" + "─" * 40)
    logger.info("Pipeline Configuration:")
    logger.info("─" * 40)
    for stage in pipeline.stages:
        components = [c.name for c in stage.components if c.enabled]
        status = "✓" if stage.enabled else "✗"
        logger.info(f"  {status} {stage.name}: {', '.join(components) if components else 'disabled'}")
    logger.info("─" * 40 + "\n")

    # Run pipeline
    success = pipeline.run()
    if success:
        logger.info("Pipeline completed successfully")
        exit(0)
    else:
        logger.error("Pipeline finished with errors")
        exit(1)


if __name__ == "__main__":
    main()