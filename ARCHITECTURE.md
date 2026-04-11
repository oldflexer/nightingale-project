# Nightingale Pipeline Architecture

## Overview

Модульная архитектура пайплайна с поддержкой:
- **Стадий (Stages)** — логические группы обработки
- **Компонентов (Components)** — отдельные обработчики с общим интерфейсом
- **PipelineContext** — контейнер данных, передаваемый между стадиями
- **Опциональные компоненты** — можно включать/выключать без изменения кода

## Стадии Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                          STAGE 1: Parsing                           │
│  ┌─────────────────┐                                               │
│  │  ParserComponent │  → fetch_latest() → PipelineContext.news_items │
│  └─────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      STAGE 2: Text Aggregation                      │
│  ┌─────────────────────────┐                                        │
│  │ TextAggregatorComponent │  → aggregated_text                     │
│  └─────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: Text Summarization                      │
│  ┌──────────────────────────┐                                       │
│  │ LLMCompressorComponent   │  → summarized_text                     │
│  └──────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              STAGE 4: Text Processing (Optional)                     │
│  ┌────────────────────┐  ┌─────────────────┐                        │
│  │ AccentorComponent  │  │ YoReplacerComp. │  → processed_text       │
│  │ (stress marks)     │  │ (Е → Ё via LLM) │                        │
│  └────────────────────┘  └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│           STAGE 5: Voice Preparation (Optional)                     │
│  ┌────────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ VoiceLoaderComp.   │→ │ STTTranscriber  │→ │ YoReplacerRef.   │  │
│  │ (VAD, audio load)  │  │ (reference)     │  │ (E → Ё in ref)   │  │
│  └────────────────────┘  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      STAGE 6: TTS Synthesis                         │
│  ┌─────────────────────────────────────────────┐                    │
│  │ TTSEngineComponent                          │  → raw_audio_path │
│  │ (uses processed_text + reference_audio)     │                    │
│  └─────────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              STAGE 7: Voice Conversion (Optional)                    │
│  ┌───────────────────────────┐                                       │
│  │ RVCComponent              │  → final_audio_path                   │
│  └───────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       STAGE 8: Publishing                           │
│  ┌───────────────────────────┐                                       │
│  │ TelegramPublisherComponent│                                       │
│  └───────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Raw Data → [news_items] → [aggregated_text] → [summarized_text] 
         → [processed_text] → [reference_text] → [raw_audio_path] 
         → [final_audio_path] → Published
```

## Component Interface

```python
class PipelineComponent(ABC):
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process context and return updated context."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Component name for logging."""
        pass
    
    @property
    def enabled(self) -> bool:
        """Whether component is active. Override for optional behavior."""
        return True
    
    def setup(self) -> None:
        """Optional setup method called before first use."""
        pass
    
    def teardown(self) -> None:
        """Optional cleanup method called after pipeline finishes."""
        pass
```

## Stage Interface

```python
class Stage(ABC):
    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute all enabled components in this stage."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name for logging."""
        pass
    
    @property
    def components(self) -> List[PipelineComponent]:
        """List of components in this stage."""
        return []
```

## Configuration-driven Pipeline

Pipeline создаётся из конфигурации:

```python
# config.yaml
pipeline:
  stages:
    - name: parsing
      enabled: true
    - name: text_processing
      enabled: true
      components:
        - name: accentor
          type: silero_stress
          enabled: true
        - name: yo_replacer
          type: llm
          enabled: false
    - name: voice_preparation
      enabled: false
    - name: tts
      enabled: true
    - name: voice_conversion
      enabled: false
    - name: publishing
      enabled: true
```

## Benefits

1. **Modularity** — каждый компонент изолирован и тестируем
2. **Flexibility** — легко добавлять/удалять компоненты
3. **Optionality** — булев флаг `enabled` для каждого компонента
4. **Testability** — можно тестировать компоненты по отдельности
5. **Extensibility** — новые компоненты реализуют интерфейс
6. **Configuration** — pipeline настраивается без изменения кода