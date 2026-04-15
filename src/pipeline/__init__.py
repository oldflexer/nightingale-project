"""Nightingale Pipeline Package - v2.0.

Refactored modular pipeline architecture following Python best practices:
- Explicit imports at module level
- Custom exception hierarchy
- Named constants instead of magic numbers
- Protocol-based interfaces for flexibility
- Immutable configuration

Pipeline Stages:
    1. Parsing - fetch news from sources
    2. Aggregation - combine news into text
    3. Summarization - compress text with LLM
    4. Text Processing - accentuation, yo replacement (optional)
    5. Voice Preparation - VAD, STT for reference (optional)
    6. Synthesis - TTS synthesis
    7. Voice Conversion - RVC (optional)
    8. Publishing - publish to channels

Example:
    >>> from src.pipeline import PipelineBuilder
    >>> pipeline = (PipelineBuilder()
    ...     .with_parsing(parser)
    ...     .with_aggregation()
    ...     .with_summarization(summarizer)
    ...     .with_tts(tts_engine)
    ...     .with_publishing(publisher)
    ...     .build())
    >>> success = pipeline.run()

See Also:
    - ARCHITECTURE.md for detailed architecture documentation
    - README.md for usage examples
"""

# Re-export core modules for convenience
from src.pipeline import constants
from src.pipeline import exceptions
from src.pipeline import interfaces
from src.pipeline import utils
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
    # Core utilities
    "utils",
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
