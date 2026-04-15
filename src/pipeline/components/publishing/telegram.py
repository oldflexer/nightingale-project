"""Telegram Publisher implementation."""

import requests
from pathlib import Path
from typing import Optional

from loguru import logger
from src.pipeline.interfaces import Publisher


class TelegramPublisher(Publisher):
    """
    Publisher for sending audio to Telegram.

    Supports both the legacy interface (Publisher.publish)
    and direct bot_token/chat_id initialization.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        # For backward compatibility, accept empty init
        self._bot_token = bot_token or ""
        self._chat_id = chat_id or ""
        self._api_url = f"https://api.telegram.org/bot{self._bot_token}" if self._bot_token else ""
        self._name = "telegram"

    def publish(self, audio_path: Path, caption: Optional[str] = None) -> bool:
        """
        Publish audio file to Telegram.

        Args:
            audio_path: Path to audio file
            caption: Optional caption for the message

        Returns:
            True if successful, False otherwise
        """
        if not self._bot_token or not self._chat_id:
            logger.warning("Telegram publisher not configured (mock mode)")
            logger.info(f"Would publish: audio={audio_path}, caption={caption}")
            return True

        logger.info(f"Publishing to Telegram (chat_id={self._chat_id})...")

        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {
                    'chat_id': self._chat_id,
                    'caption': caption or "",
                    'parse_mode': 'HTML',
                }

                response = requests.post(
                    f"{self._api_url}/sendAudio",
                    files=files,
                    data=data,
                    timeout=60
                )

            if response.ok:
                result = response.json()
                if result.get("ok"):
                    message_id = result["result"]["message_id"]
                    logger.info(f"Published successfully (message_id={message_id})")
                    return True
                else:
                    logger.error(f"Telegram API error: {result}")
                    return False
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return False

        except Exception as e:
            logger.exception(f"Telegram publishing failed: {e}")
            return False
