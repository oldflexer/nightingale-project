"""
Parser Package - news parsing components.
"""

from src.pipeline.components.parser.parser import ParserComponent
from src.pipeline.components.parser.mil_ru_parser import MilRuParser
from src.pipeline.components.parser.rss_parser import RssParser
from src.pipeline.components.parser.static_parser import StaticParser

__all__ = [
    "ParserComponent",
    "MilRuParser",
    "RssParser",
    "StaticParser",
]