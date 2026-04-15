# Nightingale Pipeline Architecture

## Overview

**Nightingale** — модульный пайплайн для автоматического создания аудио-новостей.

### Ключевые принципы

- **Pipeline Pattern** — последовательное выполнение стадий
- **Component-Based** — каждый компонент изолирован и реализует общий интерфейс
- **Optional Stages** — стадии можно включать/выключать
- **Configuration-Driven** — поведение настраивается через .env

---

## Структура проекта

```
src/
├── config.py              # Pydantic Settings
├── pipeline/
│   ├── __init__.py        # Публичный API
│   ├── core.py            # Pipeline, PipelineBuilder
│   ├── base.py            # Stage, PipelineComponent (ABC)
│   ├── interfaces.py      # Контракты: Parser, Summarizer, TTSEngine, Publisher
│   ├── context.py         # PipelineContext (data container)
│   ├── stages.py          # Определения стадий
│   ├── constants.py       # Константы (время ожидания, retry и т.д.)
│   ├── exceptions.py      # Иерархия исключений
│   └── components/
│       ├── parser/        # Парсинг новостей
│       ├── aggregation/   # Агрегация текста
│       ├── summarization/ # LLM-сжатие
│       ├── text_processing/  # Ударения, ёфикация
│       ├── voice_preparation/ # VAD, STT
│       ├── tts/           # TTS-синтез
│       ├── voice_conversion/  # RVC
│       └── publishing/    # Telegram, Discord
```

---

## Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           STAGE 1: Parsing                               │
│  ┌────────────────┐                                                       │
│  │ ParserComponent │ ──► Parser.fetch_latest() ──► PipelineContext      │
│  └────────────────┘                    .news_items                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       STAGE 2: Aggregation                               │
│  ┌───────────────────────────┐                                           │
│  │ DefaultAggregator         │ ──► NewsItem[] ──► aggregated_text       │
│  │ StructuredAggregator       │                                           │
│  └───────────────────────────┘                                           │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      STAGE 3: Summarization                              │
│  ┌────────────────────────────────────┐                                   │
│  │ LLMSummarizerComponent             │ ──► text ──► summarized_text      │
│  │   + prefix/suffix injection         │                                   │
│  └────────────────────────────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              STAGE 4: Text Processing (Optional)                         │
│  ┌──────────────────────┐  ┌─────────────────────┐                        │
│  │ SileroAccentorComponent│  │ RuleBasedYoReplacer │ ──► processed_text   │
│  │ RuaccentComponent     │  │ LLMYoReplacer       │                        │
│  └──────────────────────┘  └─────────────────────┘                        │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│               STAGE 5: Voice Preparation (Optional)                     │
│  ┌──────────────────────────┐  ┌────────────────────┐                    │
│  │ VoiceLoaderComponent      │─►│ STTTranscriber     │                    │
│  │ (VAD + audio load)       │  │                    │                    │
│  └──────────────────────────┘  └────────────────────┘                    │
│         reference_audio          reference_transcript                    │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        STAGE 6: TTS Synthesis                            │
│  ┌────────────────────────────────────────┐                               │
│  │ TTSComponent                           │ ──► raw_audio_path           │
│  │ TTSWithVoiceCloneComponent             │                              │
│  └────────────────────────────────────────┘                               │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              STAGE 7: Voice Conversion (Optional)                        │
│  ┌────────────────────────────────┐                                       │
│  │ RVCComponent                   │ ──► final_audio_path                 │
│  │ AudioEnhancementComponent      │                                      │
│  └────────────────────────────────┘                                       │
└──────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STAGE 8: Publishing                               │
│  ┌───────────────────────────────────┐                                    │
│  │ PublisherComponent                │ ──► Telegram/Discord              │
│  │ TelegramPublisherComponent        │                                    │
│  │ MultiPublisherComponent           │                                    │
│  └───────────────────────────────────┘                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Интерфейсы

### PipelineComponent (ABC)

```python
class PipelineComponent(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def enabled(self) -> bool: ...
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext: ...
    
    def setup(self) -> None: ...      # Опционально
    def teardown(self) -> None: ...   # Опционально
```

### Stage (ABC)

```python
class Stage(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def components(self) -> List[PipelineComponent]: ...
    
    def execute(self, context: PipelineContext) -> PipelineContext: ...
```

---

## PipelineContext

```python
@dataclass
class PipelineContext:
    # Input/Output fields
    news_items: list = field(default_factory=list)
    aggregated_text: str = ""
    summarized_text: str = ""
    processed_text: str = ""
    reference_audio_path: Optional[Path] = None
    reference_transcript: str = ""
    raw_audio_path: Optional[Path] = None
    final_audio_path: Optional[Path] = None
    published: bool = False
    
    # Computed properties
    text_for_synthesis: str   # processed_text → summarized_text → aggregated_text
    audio_to_publish: Path    # final_audio_path → raw_audio_path
    caption: str              # First 200 chars of text_for_synthesis
    
    # Metadata
    errors: list[str]         # Ошибки пайплайна
    warnings: list[str]       # Предупреждения
    metadata: dict[str, Any]  # Дополнительные данные
    
    # Status
    has_errors: bool         # Есть ли ошибки
    success: bool            # published=True AND not has_errors
```

---

## Builder Pattern

```python
from src.pipeline import PipelineBuilder

pipeline = (
    PipelineBuilder()
    .with_parsing(parser)
    .with_aggregation(aggregator_type="default")
    .with_summarization(summarizer, prefix="...", suffix="...")
    .with_text_processing(accentor=True, yo_replacer=False)  # Optional
    .with_voice_preparation(voice_sample_path="...", use_stt=True)  # Optional
    .with_tts(tts_engine, use_voice_clone=True)
    .with_voice_conversion(rvc_model_path="...")  # Optional
    .with_publishing(publisher)
    .build()
)

success = pipeline.run()
```

---

## Exception Hierarchy

```
PipelineError (base)
├── ConfigurationError
├── ParsingError
├── AggregationError
├── SummarizationError
├── TextProcessingError
├── VoicePreparationError
├── SynthesisError
├── VoiceConversionError
└── PublishingError
```

---

## Преимущества архитектуры

| Принцип | Описание |
|---------|----------|
| **Модульность** | Каждый компонент изолирован, легко тестировать |
| **Гибкость** | Подключение новых реализаций без изменения кода |
| **Опциональность** | `enabled=False` пропускает стадию |
| **Тестируемость** | Компоненты можно тестировать по отдельности |
| **Расширяемость** | Новая стадия = новый класс Stage |
| **Конфигурируемость** | Поведение определяется через .env |

---

## Диаграмма зависимостей

```
main.py
  └─► src/config.py (Settings)
  └─► src/pipeline (PipelineBuilder, Pipeline, Stages, Components)
        └─► src/pipeline/components/* ( implementations)
              └─► External libraries (torch, transformers, etc.)
```

---

_Дата: 2026-04-02_  
_Версия: 2.0_
