"""Application configuration with validation.

Configuration is loaded from environment variables via .env file.
All settings are validated at startup using Pydantic.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.pipeline.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VOICE_RATE,
)
from src.pipeline.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings with environment variable binding.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,  # Prevent accidental modification
    )

    # =========================================================================
    # Parser Settings
    # =========================================================================
    parser_type: Literal["mil_ru", "rss", "static"] = Field(
        default="mil_ru",
        alias="PARSER_TYPE",
    )
    news_source_url: str = Field(
        default="https://mil.ru/news",
        alias="NEWS_SOURCE_URL",
    )
    parser_use_dynamic: bool = Field(
        default=True,
        alias="PARSER_USE_DYNAMIC",
    )

    # =========================================================================
    # Summarizer Settings
    # =========================================================================
    summarizer_type: Literal["ollama", "openrouter", "mock"] = Field(
        default="ollama",
        alias="SUMMARIZER_TYPE",
    )
    summary_system_prompt: str = Field(
        default="You are a professional news anchor.",
        alias="SUMMARY_SYSTEM_PROMPT",
    )
    
    # Ollama-specific
    ollama_api_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_API_URL",
    )
    ollama_model: str = Field(
        default="deepseek-v3.2:cloud",
        alias="OLLAMA_MODEL",
    )
    ollama_timeout: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        alias="OLLAMA_TIMEOUT",
        ge=1,
        le=300,
    )
    ollama_max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        alias="OLLAMA_MAX_RETRIES",
        ge=0,
        le=10,
    )
    ollama_retry_delay: float = Field(
        default=DEFAULT_RETRY_DELAY_SECONDS,
        alias="OLLAMA_RETRY_DELAY",
        ge=0.1,
        le=60.0,
    )
    ollama_temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        alias="OLLAMA_TEMPERATURE",
        ge=0.0,
        le=2.0,
    )
    ollama_max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        alias="OLLAMA_MAX_TOKENS",
        ge=1,
        le=8192,
    )

    # =========================================================================
    # TTS Settings
    # =========================================================================
    tts_type: Literal["silero", "f5", "coqui", "mock"] = Field(
        default="silero",
        alias="TTS_TYPE",
    )
    
    # Silero TTS
    silero_language: str = Field(default="ru", alias="SILERO_LANGUAGE")
    silero_model: str = Field(default="v5_ru", alias="SILERO_MODEL")
    silero_voice: str = Field(default="aidar", alias="SILERO_VOICE")
    silero_sample_rate: int = Field(
        default=DEFAULT_SAMPLE_RATE,
        alias="SILERO_SAMPLE_RATE",
    )
    silero_use_accent_stress: bool = Field(
        default=False,
        alias="SILERO_USE_ACCENT_STRESS",
    )
    silero_put_yo: bool = Field(default=False, alias="SILERO_PUT_YO")
    silero_device: Literal["cpu", "cuda", "auto"] = Field(
        default="cpu",
        alias="SILERO_DEVICE",
    )
    silero_max_chars: int = Field(
        default=500,
        alias="SILERO_MAX_CHARS",
        ge=100,
        le=2000,
    )
    silero_silence_between_chunks: float = Field(
        default=0.2,
        alias="SILERO_SILENCE_BETWEEN_CHUNKS",
        ge=0.0,
        le=2.0,
    )
    silero_voice_rate: int = Field(
        default=DEFAULT_VOICE_RATE,
        alias="SILERO_VOICE_RATE",
        ge=50,
        le=150,
    )

    # F5-TTS
    f5_model_name: str = Field(default="", alias="F5_MODEL_NAME")
    f5_vocab: str = Field(default="", alias="F5_VOCAB")
    f5_voice_sample: Path | None = Field(default=None, alias="F5_VOICE_SAMPLE")
    f5_timeout: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        alias="F5_TIMEOUT",
    )
    f5_max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        alias="F5_MAX_RETRIES",
    )
    f5_retry_delay: float = Field(
        default=DEFAULT_RETRY_DELAY_SECONDS,
        alias="F5_RETRY_DELAY",
    )
    f5_device: Literal["cpu", "cuda", "auto"] = Field(
        default="cpu",
        alias="F5_DEVICE",
    )
    f5_use_accent_stress: bool = Field(
        default=False,
        alias="F5_USE_ACCENT_STRESS",
    )

    # Coqui TTS
    tts_model_name: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        alias="TTS_MODEL_NAME",
    )
    tts_voice_sample: Path | None = Field(
        default=None,
        alias="TTS_VOICE_SAMPLE",
    )
    tts_language: str = Field(default="ru", alias="TTS_LANGUAGE")
    tts_device: Literal["cpu", "cuda", "auto"] = Field(
        default="cpu",
        alias="TTS_DEVICE",
    )

    # =========================================================================
    # Publishing Settings
    # =========================================================================
    publisher_type: Literal["telegram", "discord", "file", "mock"] = Field(
        default="telegram",
        alias="PUBLISHER_TYPE",
    )
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    # =========================================================================
    # Validation
    # =========================================================================
    @field_validator("f5_voice_sample", "tts_voice_sample", mode="before")
    @classmethod
    def validate_path(cls, v: str | Path | None) -> Path | None:
        """Validate and convert path strings to Path objects."""
        if v is None or v == "":
            return None
        path = Path(v)
        if path.exists():
            return path
        # Allow non-existent paths for configuration (will be checked at runtime)
        return path

    @field_validator("telegram_bot_token")
    @classmethod
    def validate_bot_token_format(cls, v: str) -> str:
        """Validate Telegram bot token format."""
        if v and ":" not in v:
            raise ValueError("Telegram bot token must contain ':' separator")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This ensures settings are loaded only once and reused across the application.
    
    Returns:
        Settings instance
        
    Raises:
        ConfigurationError: If settings cannot be loaded or validated
    """
    try:
        return Settings()
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load settings: {e}",
            details={"error_type": type(e).__name__}
        ) from e


# Global settings instance for convenience
settings = get_settings()


__all__ = ["Settings", "get_settings", "settings"]

