"""Project-wide constants for Nightingale Pipeline.

This module contains all magic numbers and configuration constants
used throughout the pipeline to avoid duplication and improve readability.
"""

# =============================================================================
# Audio Constants
# =============================================================================

DEFAULT_SAMPLE_RATE: int = 24_000  
DEFAULT_VOICE_PITCH_SHIFT: int = -20  
DEFAULT_VOICE_RATE: int = 90  
DEFAULT_SILENCE_DURATION: float = 0.2  
DEFAULT_CHUNK_MAX_CHARS: int = 500
DEFAULT_CHUNK_OVERHEAD: int = 100  

# =============================================================================
# API/Network Constants
# =============================================================================

DEFAULT_TIMEOUT_SECONDS: int = 60
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_DELAY_SECONDS: float = 1.0
DEFAULT_RETRY_BACKOFF: float = 2.0

# =============================================================================
# LLM Constants
# =============================================================================

DEFAULT_MAX_TOKENS: int = 500
DEFAULT_TEMPERATURE: float = 0.5

# =============================================================================
# Publishing Constants
# =============================================================================

MAX_CAPTION_LENGTH: int = 200

# =============================================================================
# RVC Constants
# =============================================================================

RVC_MIN_PITCH: int = -12
RVC_MAX_PITCH: int = 12


__all__ = [
    "DEFAULT_SAMPLE_RATE",
    "DEFAULT_VOICE_PITCH_SHIFT", 
    "DEFAULT_VOICE_RATE",
    "DEFAULT_SILENCE_DURATION",
    "DEFAULT_CHUNK_MAX_CHARS",
    "DEFAULT_CHUNK_OVERHEAD",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY_SECONDS",
    "DEFAULT_RETRY_BACKOFF",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "MAX_CAPTION_LENGTH",
    "RVC_MIN_PITCH",
    "RVC_MAX_PITCH",
]