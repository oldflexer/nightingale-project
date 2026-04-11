"""
Nightingale Pipeline Package.

New modular pipeline architecture with stages and components.

Stages:
    1. Parsing - fetch news from sources
    2. Aggregation - combine news into text
    3. Summarization - compress text with LLM
    4. Text Processing - accentuation, yo replacement (optional)
    5. Voice Preparation - VAD, STT for reference (optional)
    6. Synthesis - TTS synthesis
    7. Voice Conversion - RVC (optional)
    8. Publishing - publish to channels

Usage:
    from src.pipeline import PipelineBuilder

    pipeline = (PipelineBuilder()
        .with_parsing(parser)
        .with_aggregation()
        .with_summarization(summarizer, prefix="...", suffix="...")
        .with_text_processing(accentor=True)
        .with_tts(tts_engine)
        .with_publishing(publisher)
        .build())

    pipeline.run()
"""

# Core classes
from src.pipeline.context import PipelineContext
from src.pipeline.base import PipelineComponent, Stage
from src.pipeline.core import Pipeline, PipelineBuilder
from src.pipeline.stages import (
    ParsingStage,
    AggregationStage,
    SummarizationStage,
    TextProcessingStage,
    VoicePreparationStage,
    SynthesisStage,
    VoiceConversionStage,
    PublishingStage,
)

# Components
from src.pipeline.components import (
    # Parsing
    ParserComponent,
    # Aggregation
    DefaultAggregator,
    StructuredAggregator,
    # Summarization
    LLMSummarizerComponent,
    PromptBasedSummarizer,
    # Text Processing
    SileroAccentorComponent,
    RuaccentComponent,
    RuleBasedYoReplacer,
    LLMYoReplacer,
    CompositeTextProcessor,
    # Voice Preparation
    VoiceLoaderComponent,
    STTTranscriberComponent,
    ReferenceYoReplacerComponent,
    # TTS
    TTSComponent,
    TTSWithVoiceCloneComponent,
    # Voice Conversion
    RVCComponent,
    AudioEnhancementComponent,
    # Publishing
    PublisherComponent,
    TelegramPublisherComponent,
    MultiPublisherComponent,
)

# Original interfaces (for compatibility) - from the new pipeline interfaces
from src.pipeline.interfaces import (
    Parser,
    Summarizer,
    TTSEngine,
    Publisher,
    TextAggregator,
    TextProcessor,
    VoiceExtractor,
    VoiceConverter,
)

__all__ = [
    # Core
    "PipelineContext",
    "PipelineComponent",
    "Stage",
    "Pipeline",
    "PipelineBuilder",
    # Stages
    "ParsingStage",
    "AggregationStage",
    "SummarizationStage",
    "TextProcessingStage",
    "VoicePreparationStage",
    "SynthesisStage",
    "VoiceConversionStage",
    "PublishingStage",
    # Components
    "ParserComponent",
    "DefaultAggregator",
    "StructuredAggregator",
    "LLMSummarizerComponent",
    "PromptBasedSummarizer",
    "SileroAccentorComponent",
    "RuaccentComponent",
    "RuleBasedYoReplacer",
    "LLMYoReplacer",
    "CompositeTextProcessor",
    "VoiceLoaderComponent",
    "STTTranscriberComponent",
    "ReferenceYoReplacerComponent",
    "TTSComponent",
    "TTSWithVoiceCloneComponent",
    "RVCComponent",
    "AudioEnhancementComponent",
    "PublisherComponent",
    "TelegramPublisherComponent",
    "MultiPublisherComponent",
    # Interfaces
    "Parser",
    "Summarizer",
    "TTSEngine",
    "Publisher",
    "TextAggregator",
    "TextProcessor",
    "VoiceExtractor",
    "VoiceConverter",
]