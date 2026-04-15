# Nightingale — План разработки

## 1. Цели и требования

**Nightingale** — модульный Python-пайплайн для автоматизации создания аудио-новостей:

- Сбор новостей с заданного источника (mil.ru)
- Обработка текста LLM (сжатие/пересказ через Ollama или OpenRouter)
- Синтез речи локальной TTS-моделью (Silero, F5-TTS, Coqui)
- Публикация аудио в Telegram-канал

### Ключевые нефункциональные требования

- **Сменяемость компонентов** — легко заменить источник, LLM, TTS, канал публикации
- **Конфигурация через .env** — pydantic-settings с валидацией
- **Pipeline-архитектура** — 8 стадий с опциональными компонентами
- **Логирование и обработка ошибок** — loguru + retry-логика

---

## 2. Архитектура

### Компонентная модель

```
src/pipeline/
├── components/              # Реализации компонентов
│   ├── parser/              # Парсинг (mil_ru, rss, static)
│   ├── aggregation/         # Агрегация текста
│   ├── summarization/       # LLM-сжатие (ollama, openrouter)
│   ├── text_processing/     # Обработка текста (ударения, ёфикация)
│   ├── voice_preparation/   # VAD, STT для клонирования
│   ├── tts/                 # TTS (silero, f5, coqui)
│   ├── voice_conversion/     # RVC
│   └── publishing/           # Telegram, Discord, file
├── core.py                  # Pipeline, PipelineBuilder
├── base.py                  # Stage, PipelineComponent
├── interfaces.py            # Абстрактные интерфейсы
└── context.py               # PipelineContext
```

### Интерфейсы

| Интерфейс | Метод | Описание |
|-----------|-------|----------|
| `Parser` | `fetch_latest() -> List[NewsItem]` | Получение новостей |
| `Summarizer` | `summarize(text) -> str` | LLM-сжатие текста |
| `TTSEngine` | `synthesize(text, path) -> Path` | Синтез речи |
| `Publisher` | `publish(path, caption) -> bool` | Публикация аудио |

---

## 3. Стадии Pipeline

```
┌────────────────────┐
│ 1. Parsing         │  → news_items
└────────────────────┘
            ↓
┌────────────────────┐
│ 2. Aggregation     │  → aggregated_text
└────────────────────┘
            ↓
┌────────────────────┐
│ 3. Summarization   │  → summarized_text
└────────────────────┘
            ↓
┌────────────────────┐
│ 4. Text Processing │  → processed_text (опц.)
└────────────────────┘
            ↓
┌────────────────────┐
│ 5. Voice Prep      │  → reference_audio, transcript (опц.)
└────────────────────┘
            ↓
┌────────────────────┐
│ 6. TTS Synthesis   │  → raw_audio
└────────────────────┘
            ↓
┌────────────────────┐
│ 7. Voice Conversion│  → final_audio (опц.)
└────────────────────┘
            ↓
┌────────────────────┐
│ 8. Publishing      │  → Telegram/Discord
└────────────────────┘
```

---

## 4. Конфигурация

### Переменные окружения (.env)

```bash
# Parser
PARSER_TYPE=mil_ru
NEWS_SOURCE_URL=https://mil.ru/news
PARSER_USE_DYNAMIC=true

# Summarizer
SUMMARIZER_TYPE=ollama
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-v3.2:cloud
SUMMARY_SYSTEM_PROMPT="Ты — профессиональный диктор новостей."

# TTS
TTS_TYPE=silero
SILERO_LANGUAGE=ru
SILERO_VOICE=aidar

# Publisher
PUBLISHER_TYPE=telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
```

---

## 5. Статус реализации

| Компонент | Статус | Реализации |
|-----------|--------|------------|
| Parser | ✅ Готово | MilRuParser |
| Aggregator | ✅ Готово | DefaultAggregator, StructuredAggregator |
| Summarizer | ✅ Готово | OllamaSummarizer, OpenRouterSummarizer |
| Text Processor | ✅ Готово | SileroAccentor, Ruaccent, YoReplacer |
| Voice Preparation | ✅ Готово | VoiceLoader, STTTranscriber |
| TTS | ✅ Готово | SileroTTS, F5TTS, CoquiTTS |
| Voice Conversion | 🔧 В разработке | RVCComponent (stub) |
| Publisher | ✅ Готово | TelegramPublisher |

---

## 6. Следующие шаги

1. **Интеграционные тесты** — pytest с моками
2. **Кэширование** — сохранение результатов между запусками
3. **Расписание** — apscheduler для автоматических запусков
4. **Мониторинг** — метрики, алерты при ошибках
5. **CLI** — click/typer для управления

---

_Дата: 2026-04-02_  
_Версия: 2.0_
