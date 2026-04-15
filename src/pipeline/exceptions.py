"""Custom exceptions for Nightingale Pipeline.

All exceptions inherit from PipelineError for consistent error handling.
"""


class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing."""
    pass


class ParsingError(PipelineError):
    """Raised when news parsing fails."""
    pass


class AggregationError(PipelineError):
    """Raised when text aggregation fails."""
    pass


class SummarizationError(PipelineError):
    """Raised when text summarization fails."""
    pass


class TextProcessingError(PipelineError):
    """Raised when text processing (accentuation, etc.) fails."""
    pass


class VoicePreparationError(PipelineError):
    """Raised when voice preparation (VAD, STT) fails."""
    pass


class SynthesisError(PipelineError):
    """Raised when TTS synthesis fails."""
    pass


class VoiceConversionError(PipelineError):
    """Raised when voice conversion (RVC) fails."""
    pass


class PublishingError(PipelineError):
    """Raised when publishing fails."""
    pass


__all__ = [
    "PipelineError",
    "ConfigurationError",
    "ParsingError",
    "AggregationError",
    "SummarizationError",
    "TextProcessingError",
    "VoicePreparationError",
    "SynthesisError",
    "VoiceConversionError",
    "PublishingError",
]