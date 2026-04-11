"""
Pipeline Stages - логические группы компонентов.
"""
from typing import Optional, List

from src.pipeline.base import Stage, PipelineComponent
from src.pipeline.context import PipelineContext


class ParsingStage(Stage):
    """
    Stage 1: Parsing
    
    Компоненты:
    - ParserComponent: получение новостей из источника
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="parsing", enabled=enabled)


class AggregationStage(Stage):
    """
    Stage 2: Text Aggregation
    
    Компоненты:
    - DefaultAggregator: стандартная агрегация новостей
    - StructuredAggregator: структурированная агрегация
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="aggregation", enabled=enabled)


class SummarizationStage(Stage):
    """
    Stage 3: Text Summarization
    
    Компоненты:
    - LLMSummarizerComponent: сжатие текста через LLM
    - PromptBasedSummarizer: добавление префикса/суффикса
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="summarization", enabled=enabled)


class TextProcessingStage(Stage):
    """
    Stage 4: Text Processing (Optional)
    
    Компоненты:
    - SileroAccentorComponent: расстановка ударений
    - RuaccentComponent: альтернативный акцентуатор
    - RuleBasedYoReplacer: замена Е на Ё (правила)
    - LLMYoReplacer: замена Е на Ё (LLM)
    - CompositeTextProcessor: композитный процессор
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="text_processing", enabled=enabled)


class VoicePreparationStage(Stage):
    """
    Stage 5: Voice Preparation (Optional)
    
    Компоненты:
    - VoiceLoaderComponent: VAD, загрузка аудио
    - STTTranscriberComponent: транскрибация референса
    - ReferenceYoReplacerComponent: Ёфикация транскрипта
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="voice_preparation", enabled=enabled)


class SynthesisStage(Stage):
    """
    Stage 6: TTS Synthesis
    
    Компоненты:
    - TTSComponent: базовый синтез
    - TTSWithVoiceCloneComponent: синтез с клонированием голоса
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="synthesis", enabled=enabled)


class VoiceConversionStage(Stage):
    """
    Stage 7: Voice Conversion (Optional)
    
    Компоненты:
    - RVCComponent: преобразование голоса
    - AudioEnhancementComponent: улучшение качества
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="voice_conversion", enabled=enabled)


class PublishingStage(Stage):
    """
    Stage 8: Publishing
    
    Компоненты:
    - PublisherComponent: базовая публикация
    - TelegramPublisherComponent: публикация в Telegram
    - MultiPublisherComponent: публикация в несколько каналов
    """
    
    def __init__(self, enabled: bool = True):
        super().__init__(name="publishing", enabled=enabled)
