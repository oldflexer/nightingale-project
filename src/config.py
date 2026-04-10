from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Parser
    parser_type: str = Field(default="mil_ru", alias="PARSER_TYPE")
    news_source_url: str = Field(default="https://mil.ru/news", alias="NEWS_SOURCE_URL")
    parser_use_dynamic: bool = Field(default=True, alias="PARSER_USE_DYNAMIC")

    # Summarizer
    summarizer_type: str = Field(default="openrouter", alias="SUMMARIZER_TYPE")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="arcee-ai/trinity", alias="OPENROUTER_MODEL")
    summary_system_prompt: str = Field(
        default="You are a news anchor. Make a concise summary in Russian.",
        alias="SUMMARY_SYSTEM_PROMPT"
    )

    # Ollama
    ollama_api_url: str = Field(default="http://localhost:11434", alias="OLLAMA_API_URL")
    ollama_model: str = Field(default="deepseek-v3.2:cloud", alias="OLLAMA_MODEL")
    ollama_timeout: int = Field(default=60, alias="OLLAMA_TIMEOUT")
    ollama_max_retries: int = Field(default=3, alias="OLLAMA_MAX_RETRIES")
    ollama_retry_delay: float = Field(default=1.0, alias="OLLAMA_RETRY_DELAY")
    ollama_temperature: float = Field(default=0.5, alias="OLLAMA_TEMPERATURE")
    ollama_max_tokens: int = Field(default=500, alias="OLLAMA_MAX_TOKENS")

    # TTS
    tts_type: str = Field(default="coqui", alias="TTS_TYPE")

    # coqui
    tts_model_name: str = Field(default="tts_models/multilingual/multi-dataset/xtts_v2", alias="TTS_MODEL_NAME")
    tts_voice_sample: str = Field(default="", alias="TTS_VOICE_SAMPLE")
    tts_language: str = Field(default="ru", alias="TTS_LANGUAGE")
    tts_device: str = Field(default="auto", alias="TTS_DEVICE") # "cuda", "cpu" или "auto"

    # F5-TTS
    f5_model_name: str = Field(default="models/F5TTS_v1_Base_v2/model_last_inference.safetensors", alias="F5_MODEL_NAME")
    f5_vocab: str = Field(default="models/F5TTS_v1_Base_v2/vocab.txt", alias="F5_VOCAB")
    f5_voice_sample: str = Field(default="", alias="F5_VOICE_SAMPLE")
    f5_timeout: int = Field(default=300, alias="F5_TIMEOUT")
    f5_max_retries: int = Field(default=3, alias="F5_MAX_RETRIES")
    f5_retry_delay: float = Field(default=1.0, alias="F5_RETRY_DELAY")
    f5_device: str = Field(default="cpu", alias="F5_DEVICE")
    f5_use_accent_stress: bool = Field(default=True, alias="F5_USE_ACCENT_STRESS")

    # vocos
    vocos_path: str = Field(default="", alias="VOCOS_PATH")

    # Silero TTS
    silero_language: str = Field(default="ru", alias="SILERO_LANGUAGE")
    silero_model: str = Field(default="v5_ru", alias="SILERO_MODEL")
    silero_voice: str = Field(default="aidar", alias="SILERO_VOICE")
    silero_sample_rate: int = Field(default=24000, alias="SILERO_SAMPLE_RATE")
    silero_use_accent_stress: bool = Field(default=False, alias="SILERO_USE_ACCENT_STRESS")
    silero_put_yo: bool = Field(default=False, alias="SILERO_PUT_YO")
    silero_device: str = Field(default="cpu", alias="SILERO_DEVICE")
    silero_max_chars: int = Field(default=500, alias="SILERO_MAX_CHARS")
    silero_silence_between_chunks: float = Field(default=0.2, alias="SILERO_SILENCE_BETWEEN_CHUNKS")
    
    # Настройки ruaccent
    f5_use_ruaccent: bool = Field(default=True, alias="F5_USE_RUACCENT")
    ruaccent_model_size: str = Field(default="turbo3.1", alias="RUACCENT_MODEL_SIZE")

    # Publisher
    publisher_type: str = Field(default="telegram", alias="PUBLISHER_TYPE")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()