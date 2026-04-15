"""
Pipeline utilities.

Shared helper functions used across pipeline components.
"""
import time
from collections.abc import Callable
from typing import TypeVar

from loguru import logger


T = TypeVar("T")


def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    **kwargs,
) -> T:
    """
    Execute a function with exponential backoff retry.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exception types to catch and retry
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all retries fail
    """
    last_exception: BaseException | None = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
            
            if attempt < max_retries:
                delay = base_delay * (backoff_factor ** (attempt - 1))
                logger.debug(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
    
    assert last_exception is not None  # guaranteed after retry loop
    raise last_exception


def split_text_by_sentences(
    text: str,
    max_chars: int = 250,
    overhead: int = 100,
) -> list[str]:
    """
    Split text into chunks by sentences, respecting max_chars.
    
    Args:
        text: Input text to split
        max_chars: Maximum characters per chunk (excluding overhead)
        overhead: Estimated overhead for SSML/formatting tags
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Split into sentences
    sentences = []
    current = ""
    
    for char in text:
        current += char
        if char in ".!?":
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    
    # Combine sentences into chunks
    chunks = []
    current_chunk = ""
    
    for sent in sentences:
        if len(current_chunk) + len(sent) + 1 + overhead <= max_chars:
            current_chunk = (current_chunk + " " + sent).strip() if current_chunk else sent
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sent
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # Fallback for very long sentences
    if not chunks:
        words = text.split()
        chunk_size = max(1, (max_chars - overhead) // 10)
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
    
    logger.debug(f"Split text into {len(chunks)} chunks (max {max_chars} chars)")
    return chunks


def format_enumeration(news_items: list, ordinal_formatter: Callable[[int], str]) -> str:
    """
    Format a list of news items with ordinal numbers.
    
    Args:
        news_items: List of items to format
        ordinal_formatter: Function that converts number to ordinal (e.g., "1" -> "first")
    
    Returns:
        Formatted string with enumerated items
    """
    if not news_items:
        return ""
    
    parts = []
    for i, item in enumerate(news_items, 1):
        ordinal = ordinal_formatter(i)
        if hasattr(item, 'title') and hasattr(item, 'content_text'):
            parts.append(f"{ordinal}: {item.title}. {item.content_text}")
        else:
            title = getattr(item, 'title', 'No title')
            content = getattr(item, 'content_text', str(item))
            parts.append(f"{ordinal}: {title}. {content}")
    
    return " ".join(parts)