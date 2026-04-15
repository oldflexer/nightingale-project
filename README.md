# 🎙️ Nightingale

**Nightingale** — модульный Python-пайплайн для автоматического создания и публикации аудио-новостей.

## Возможности

- 🕸️ **Парсинг новостей** — MilRu, RSS, статические источники
- 🧠 **LLM-сжатие текста** — Ollama, OpenRouter
- 🎧 **Синтез речи** — Silero TTS, F5-TTS, Coqui XTTS
- 🔧 **Обработка текста** — расстановка ударений, ёфикация
- 🎙️ **Клонирование голоса** — VAD + STT для референса
- 📤 **Публикация** — Telegram, Discord

## Установка

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/nightingale.git
cd nightingale

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Зависимости
pip install -r requirements.txt

# Playwright (для динамического контента)
playwright install chromium
```

## Конфигурация

Создайте файл `.env` в корне проекта:

```bash
# Parser
PARSER_TYPE=mil_ru
NEWS_SOURCE_URL=https://mil.ru/news
PARSER_USE_DYNAMIC=true

# Summarizer (Ollama)
SUMMARIZER_TYPE=ollama
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-v3.2:cloud
SUMMARY_SYSTEM_PROMPT="Ты — профессиональный диктор новостей."

# TTS
TTS_TYPE=silero
SILERO_LANGUAGE=ru
SILERO_VOICE=aidar
SILERO_DEVICE=cpu

# Voice Cloning (опционально)
F5_VOICE_SAMPLE=/path/to/voice.wav

# Publisher
PUBLISHER_TYPE=telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Использование

### Запуск пайплайна

```bash
python main.py
```

### Python API

```python
from src.pipeline import PipelineBuilder
from src.pipeline.components.parser import MilRuParser
from src.pipeline.components.summarization import OllamaSummarizer
from src.pipeline.components.tts import SileroTTSEngine
from src.pipeline.components.publishing import TelegramPublisher

# Создание компонентов
parser = MilRuParser(use_dynamic=True)
summarizer = OllamaSummarizer(api_url="http://localhost:11434", model="deepseek-v3.2:cloud")
tts = SileroTTSEngine(language="ru", voice="aidar")
publisher = TelegramPublisher(bot_token="xxx", chat_id="yyy")

# Построение пайплайна
pipeline = (
    PipelineBuilder()
    .with_parsing(parser)
    .with_aggregation()
    .with_summarization(summarizer, prefix="Внимание! Говорит Москва! ")
    .with_tts(tts, use_voice_clone=False)
    .with_publishing(publisher)
    .build()
)

# Запуск
success = pipeline.run()
```

### Опциональные стадии

```python
pipeline = (
    PipelineBuilder()
    .with_parsing(parser)
    .with_aggregation()
    .with_summarization(summarizer)
    
    # Обработка текста
    .with_text_processing(accentor=True, accentor_type="silero", yo_replacer=True)
    
    # Подготовка голоса для клонирования
    .with_voice_preparation(voice_sample_path="/path/to/voice.wav", use_stt=True)
    
    .with_tts(tts, use_voice_clone=True)
    
    # RVC (опционально)
    .with_voice_conversion(rvc_model_path="/path/to/model.pth")
    
    .with_publishing(publisher)
    .build()
)
```

## Архитектура

```
┌─────────┐   ┌──────────┐   ┌────────────┐   ┌──────┐   ┌────────┐
│ Parsing │ → │Aggregation│ → │Summarization│ → │ TTS  │ → │Publish │
└─────────┘   └──────────┘   └────────────┘   └──────┘   └────────┘
                                                        
     Optional: Text Processing, Voice Preparation, Voice Conversion
```

Подробности см. в [ARCHITECTURE.md](ARCHITECTURE.md).

## Требования

- Python 3.10+
- Ollama (для локальной LLM) или OpenRouter API
- Telegram Bot Token

## Разработка

```bash
# Тесты
pytest tests/

# Линтер
ruff check src/

# Форматирование
ruff format src/
```

## Лицензия

Apache 2.0

---

_Автор: Ivan Melentyev (oldflexer)_  
_Версия: 2.0_
