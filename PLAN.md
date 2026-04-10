# 🎙️ Nightingale — План разработки

## 1. Цели и требования

Разработать модульный Python-пайплайн для:

- Сбора новостей с заданного источника (mil.ru).
- Обработки текста LLM (сжатие/пересказ через OpenRouter).
- Синтеза речи локальной TTS-моделью.
- Публикации аудио в Telegram-канал.

**Ключевые нефункциональные требования:**

- Сменяемость компонентов (легко заменить источник, LLM, TTS, место публикации).
- Конфигурация через `.env` или YAML.
- Возможность запуска по расписанию и вручную.
- Логирование, обработка ошибок, повторные попытки.

## 2. Архитектура (модули и интерфейсы)

### 2.1. Parser (Абстрактный класс)

Ответственность: извлечение списка новостей с источника.

Интерфейс:

```python
class Parser(ABC):
    def fetch_latest(self) -> List[NewsItem]: ...
```

- NewsItem — dataclass с полями: title, url, content_text, date (опционально).

- Может быть реализован как MilRuParser, RssParser, StaticHtmlParser и т.д.

- Внутренняя логика: HTTP-запросы, парсинг (BeautifulSoup/Playwright/Selenium).

### 2.2. TextAggregator

Ответственность: объединить все новости в один «сырой» текст для LLM.

- Простой конкатенатор: заголовок + текст каждой новости с разделителями.

- Может поддерживать шаблоны форматирования (настраивается через конфиг).

### 2.3. Summarizer (Абстрактный класс)

Ответственность: отправить текст LLM и получить краткую выжимку.

Интерфейс:

```python
class Summarizer(ABC):
    def summarize(self, raw_text: str) -> str: ...
```

- Реализации: OpenRouterSummarizer, LocalLLMSummarizer, MockSummarizer.

- Параметры: модель, системный промпт, максимальная длина.

- Включает обработку ошибок API, повторные попытки.

### 2.4. TTSEngine (Абстрактный класс)

Ответственность: синтез речи из текста в аудиофайл.

Интерфейс:

```python
class TTSEngine(ABC):
    def synthesize(self, text: str, output_path: Path) -> Path: ...
    # или возвращает bytes/io.BytesIO
```

- Реализации: CoquiTTS, EdgeTTS, SileroTTS, MockTTS.

- Параметры: язык, голос (speaker_wav для клонирования), скорость, формат.

### 2.5. Publisher (Абстрактный класс)

Ответственность: отправить аудиофайл в целевой канал.

Интерфейс:

```python
class Publisher(ABC):
    def publish(self, audio_path: Path, caption: Optional[str] = None) -> bool: ...
```

- Реализации: TelegramPublisher, DiscordPublisher, LocalFilePublisher.

- Telegram: использует бот-токен и chat_id из конфига.

### 2.6. Оркестратор (Pipeline)

Ответственность: последовательный вызов модулей, обработка ошибок, кэширование, логирование.

- Примерный псевдокод:

```python
def run():
    news = parser.fetch_latest()
    if not news: log and exit
    raw = aggregator.aggregate(news)
    summary = summarizer.summarize(raw)
    audio = tts.synthesize(summary)
    publisher.publish(audio, caption=summary[:200])
```

- Поддерживает fallback: если LLM недоступен — использовать сырой текст (или предыдущую успешную выжимку).

### 2.7. Конфигурация

- Использовать pydantic-settings или python-dotenv + dataclass.

- Пример .env:

```
# Parser
NEWS_SOURCE_URL=https://mil.ru/news
PARSER_TYPE=mil_ru

# Summarizer
SUMMARIZER_TYPE=openrouter
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=arcee-ai/trinity
SUMMARY_SYSTEM_PROMPT="..."  # опционально
MAX_SUMMARY_TOKENS=500

# TTS
TTS_TYPE=coqui
TTS_API_URL=http://localhost:5002/api/tts
TTS_VOICE_SAMPLE=/app/voice-samples/levitan.wav
TTS_LANGUAGE=ru

# Publisher
PUBLISHER_TYPE=telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

## 3. Этапы разработки (спринты)

### Спринт 0: Настройка окружения и скелет
- Создать репозиторий, requirements.txt.

- Реализовать абстрактные классы (интерфейсы) в отдельных модулях.

- Написать базовый Pipeline с заглушками.

### Спринт 1: Парсер mil.ru
- Реализовать MilRuParser:

    - GET https://mil.ru/news.

    - Извлечь список новостей (CSS-селекторы по классам, которые используются на сайте).

    - Для каждой новости получить полный текст (переход по ссылке или встроенный контент).

- Unit-тесты на фикстурах (сохранённый HTML).

- Обработка сетевых ошибок, таймаутов.

### Спринт 2: Интеграция с OpenRouter (LLM)
- Реализовать OpenRouterSummarizer:

    - HTTP POST к https://openrouter.ai/api/v1/chat/completions.

    - Системный промпт: «Ты — диктор новостей. Сделай краткую выжимку из предоставленного текста. Обязательно добавь фразы ...»

    - Обработка ответа, извлечение текста.

- Добавить повторные попытки (retry с exponential backoff).

### Спринт 3: TTS (локальный Coqui)
- Реализовать CoquiTTS:

    - POST запрос к http://localhost:5002/api/tts.

    - Параметры: text, speaker_wav, language.

    - Получение аудио (WAV) и сохранение во временный файл.

- Опционально: запуск Coqui-сервера через Docker (инструкция в README).

### Спринт 4: Telegram-публикация
- Реализовать TelegramPublisher:

    - Использовать python-telegram-bot или прямой REST к api.telegram.org.

    - Отправка аудио как sendAudio с подписью (caption).

- Проверка прав бота, обработка ошибок.

### Спринт 5: Оркестратор и скрипт запуска
- Связать все модули в main.py.

- Добавить аргументы командной строки: --dry-run (без публикации), --force (игнорировать кэш).

- Логирование (уровни INFO, DEBUG, ERROR) в файл и консоль.

### Спринт 6: Расписание и кэширование
- Встроить schedule или apscheduler для запуска каждый час.

- Кэш: хранить последний успешный результат (текст + аудио), чтобы при ошибке LLM/TTS отправить предыдущее.

- Простейший кэш на диске (JSON + аудиофайлы).

### Спринт 7: Тестирование и документация
- Модульные тесты для каждого компонента (с моками).

- Интеграционные тесты (опционально, с реальными API в CI не рекомендуется).

- README: установка, настройка, запуск, переменные окружения, примеры.

---

#### ___Дата составления: 2026-04-02___
#### ___Версия плана: 1.0___