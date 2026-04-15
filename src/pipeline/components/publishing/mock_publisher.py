"""
Mock Publishers - for testing without external services.
"""
from pathlib import Path
from loguru import logger

from src.pipeline.interfaces import Publisher


class MockPublisher(Publisher):
    """Mock publisher that logs but doesn't actually publish."""

    def publish(self, audio_path: Path, caption: str | None = None) -> bool:
        """Mock publish - always returns True."""
        logger.info(f"[MockPublisher] Would publish: {audio_path}")
        logger.info(f"[MockPublisher] Caption: {caption[:50] if caption else 'None'}...")
        return True


class FilePublisher(Publisher):
    """Publisher that saves audio to a local file."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def publish(self, audio_path: Path, caption: str | None = None) -> bool:
        """Copy audio to output directory."""
        import shutil
        
        try:
            output_path = self.output_dir / audio_path.name
            shutil.copy2(audio_path, output_path)
            logger.info(f"[FilePublisher] Saved to: {output_path}")
            
            if caption:
                caption_path = output_path.with_suffix('.txt')
                caption_path.write_text(caption, encoding='utf-8')
                logger.info(f"[FilePublisher] Saved caption to: {caption_path}")
            
            return True
        except Exception as e:
            logger.error(f"[FilePublisher] Failed: {e}")
            return False


class DiscordPublisher(Publisher):
    """Discord webhook publisher (placeholder)."""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
    
    def publish(self, audio_path: Path, caption: str | None = None) -> bool:
        """Mock Discord publish."""
        logger.warning("[DiscordPublisher] Not implemented - using mock")
        logger.info(f"[DiscordPublisher] Would post: {audio_path}")
        return True
