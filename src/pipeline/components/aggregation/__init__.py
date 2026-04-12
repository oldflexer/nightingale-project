"""
Aggregation Package - text aggregation components.
"""

from src.pipeline.components.aggregation.aggregator import (
    DefaultAggregator,
    StructuredAggregator,
)

# Alias for convenience
Aggregator = DefaultAggregator

__all__ = [
    "DefaultAggregator",
    "StructuredAggregator",
    "Aggregator",
]