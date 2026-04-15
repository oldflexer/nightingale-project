"""Nightingale - News to Telegram Audio Pipeline.

Main entry point using the modular pipeline architecture.
"""

from pathlib import Path

from loguru import logger

from src.config import settings


def main() -> None:
    """Run the Nightingale news-to-audio pipeline."""
    # Configure logging
    _setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting Nightingale Pipeline")
    logger.info("=" * 60)
    
    # Create components based on settings
    parser = _create_parser()
    summarizer = _create_summarizer()
    tts_engine = _create_tts()
    publisher = _create_publisher()
    
    # Build and run pipeline
    pipeline = _build_pipeline(
        parser=parser,
        summarizer=summarizer,
        tts_engine=tts_engine,
        publisher=publisher,
    )
    
    # Print configuration summary
    _log_pipeline_config(pipeline)
    
    # Execute
    success = pipeline.run()
    
    if success:
        logger.info("Pipeline completed successfully")
    else:
        logger.error("Pipeline finished with errors")
    
    exit(0 if success else 1)


def _setup_logging() -> None:
    """Configure application logging."""
    log_file = Path("nightingale.log")
    if log_file.exists():
        log_file.unlink()
    
    logger.add(
        "nightingale.log",
        level="DEBUG",
        format="{time} | {level} | {name}:{function}:{line} | {message}",
    )


def _create_parser():
    """Create parser based on settings."""
    parser_type = settings.parser_type
    
    if parser_type == "mil_ru":
        from src.pipeline.components.parser import MilRuParser
        return MilRuParser(
            use_dynamic=settings.parser_use_dynamic,
            timeout=20,
        )
    elif parser_type == "rss":
        from src.pipeline.components.parser import RssParser
        return RssParser(source_url=settings.news_source_url)
    elif parser_type == "static":
        from src.pipeline.components.parser import StaticParser
        return StaticParser(source_url=settings.news_source_url)
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")


def _create_summarizer():
    """Create summarizer based on settings."""
    summarizer_type = settings.summarizer_type
    
    if summarizer_type == "ollama":
        from src.pipeline.components.summarization import OllamaSummarizer
        return OllamaSummarizer(
            api_url=settings.ollama_api_url,
            model=settings.ollama_model,
            system_prompt=settings.summary_system_prompt,
            timeout=settings.ollama_timeout,
            max_retries=settings.ollama_max_retries,
            retry_delay=settings.ollama_retry_delay,
            temperature=settings.ollama_temperature,
            max_tokens=settings.ollama_max_tokens,
        )
    elif summarizer_type == "openrouter":
        from src.pipeline.components.summarization import OpenRouterSummarizer
        return OpenRouterSummarizer()
    elif summarizer_type == "mock":
        from src.pipeline.components.summarization import MockSummarizer
        return MockSummarizer()
    else:
        raise ValueError(f"Unknown summarizer type: {summarizer_type}")


def _create_tts():
    """Create TTS engine based on settings."""
    tts_type = settings.tts_type
    
    if tts_type == "silero":
        from src.pipeline.components.tts import SileroTTSEngine
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
    elif tts_type == "f5":
        from src.pipeline.components.tts import F5TTSEngine
        return F5TTSEngine(
            model_path=settings.f5_model_name,
            vocab_path=settings.f5_vocab,
            device=settings.f5_device,
        )
    elif tts_type == "coqui":
        from src.pipeline.components.tts import CoquiTTSEngine
        return CoquiTTSEngine(
            model_name=settings.tts_model_name,
            device=settings.tts_device,
        )
    elif tts_type == "mock":
        from src.pipeline.components.tts import MockTTSEngine
        return MockTTSEngine(sample_rate=settings.silero_sample_rate)
    else:
        raise ValueError(f"Unknown TTS type: {tts_type}")


def _create_publisher():
    """Create publisher based on settings."""
    publisher_type = settings.publisher_type
    
    if publisher_type == "telegram":
        from src.pipeline.components.publishing import TelegramPublisher
        return TelegramPublisher(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        )
    elif publisher_type == "discord":
        from src.pipeline.components.publishing import DiscordPublisher
        return DiscordPublisher()
    elif publisher_type == "file":
        from src.pipeline.components.publishing import FilePublisher
        return FilePublisher()
    elif publisher_type == "mock":
        from src.pipeline.components.publishing import MockPublisher
        return MockPublisher()
    else:
        raise ValueError(f"Unknown publisher type: {publisher_type}")


def _build_pipeline(parser, summarizer, tts_engine, publisher):
    """Build the pipeline with all components."""
    from src.pipeline import PipelineBuilder
    
    use_voice_clone = bool(settings.f5_voice_sample)
    
    return (
        PipelineBuilder()
        .with_parsing(parser)
        .with_aggregation(aggregator_type="default")
        .with_summarization(
            summarizer,
            prefix="Внимание! Говорит Москва! Передаем важное правительственное сообщение!... ",
            suffix=" Наше дело правое! Враг будет разбит! Победа будет за нами!...",
        )
        # Optional: Text Processing
        # .with_text_processing(accentor=True, accentor_type="silero", yo_replacer=False)
        
        # Optional: Voice Preparation
        # .with_voice_preparation(voice_sample_path=settings.f5_voice_sample, use_stt=True)
        
        .with_tts(tts_engine, use_voice_clone=use_voice_clone)
        
        # Optional: Voice Conversion
        # .with_voice_conversion(rvc_model_path="models/rvc/model.pth")
        
        .with_publishing(publisher)
        .build()
    )


def _log_pipeline_config(pipeline) -> None:
    """Log pipeline configuration summary."""
    logger.info("\n" + "─" * 40)
    logger.info("Pipeline Configuration:")
    logger.info("─" * 40)
    
    for stage in pipeline.stages:
        components = [c.name for c in stage.components if c.enabled]
        status = "✓" if stage.enabled else "✗"
        logger.info(
            f"  {status} {stage.name}: "
            f"{', '.join(components) if components else 'disabled'}"
        )
    
    logger.info("─" * 40 + "\n")


if __name__ == "__main__":
    main()