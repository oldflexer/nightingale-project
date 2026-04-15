"""
Stage 8: Publishing components.
"""

import requests
from pathlib import Path
from typing import Optional

from src.pipeline.base import PipelineComponent
from src.pipeline.context import PipelineContext
from src.pipeline.interfaces import Publisher


class PublisherComponent(PipelineComponent):
    """
    Компонент публикации аудио.
    
    Использует Publisher для публикации в Telegram/другие каналы.
    Результат сохраняется в context.published.
    """
    
    def __init__(
        self,
        publisher: Optional[Publisher] = None,
        enabled: bool = True,
    ):
        super().__init__(name="publisher", enabled=enabled)
        self._publisher = publisher
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        audio_path = context.audio_to_publish
        if audio_path is None or not audio_path.exists():
            self._logger.error("No audio to publish")
            context.add_error("Publisher: no audio file available")
            return context
        
        caption = context.caption
        self._logger.info(
            f"Publishing audio ({audio_path.name}, "
            f"caption: {len(caption)} chars)..."
        )
        
        if self._publisher is None:
            self._logger.error("No publisher configured")
            context.add_error("Publisher: no publisher configured")
            return context
        
        try:
            success = self._publisher.publish(
                audio_path=audio_path,
                caption=caption
            )
            
            if success:
                context.published = True
                self._logger.info("Audio published successfully")
            else:
                context.published = False
                context.publish_error = "Publisher returned failure"
                self._logger.error("Publishing failed")
            
        except Exception as e:
            self._logger.exception(f"Publishing failed: {e}")
            context.published = False
            context.publish_error = str(e)
            context.add_error(f"Publisher failed: {e}")
        
        return context


class TelegramPublisherComponent(PublisherComponent):
    """
    Компонент публикации в Telegram.
    
    Использует TelegramBot API для отправки аудио.
    """
    
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enabled: bool = True,
    ):
        super().__init__(
            publisher=None,  # Will be created in setup
            enabled=enabled
        )
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def setup(self) -> None:
        """Test Telegram connection."""
        self._logger.info("Testing Telegram connection...")
        try:
            response = requests.get(
                f"{self._api_url}/getMe",
                timeout=10
            )
            if response.ok:
                bot_info = response.json()
                if bot_info.get("ok"):
                    self._logger.info(
                        f"Telegram bot connected: @{bot_info['result']['username']}"
                    )
                else:
                    self._logger.warning("Telegram bot not authorized")
            else:
                self._logger.warning(f"Telegram API error: {response.status_code}")
        except Exception as e:
            self._logger.warning(f"Telegram connection test failed: {e}")
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        audio_path = context.audio_to_publish
        if audio_path is None or not audio_path.exists():
            self._logger.error("No audio to publish")
            context.add_error("Publisher: no audio file available")
            return context
        
        caption = context.caption
        self._logger.info(
            f"Publishing to Telegram ({audio_path.name}, "
            f"chat_id: {self._chat_id})..."
        )
        
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {
                    'chat_id': self._chat_id,
                    'caption': caption,
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
                    message = result["result"]["message"]
                    message_id = message["message_id"]
                    self._logger.info(
                        f"Published successfully (message_id: {message_id})"
                    )
                    context.published = True
                    context.metadata["telegram_message_id"] = message_id
                else:
                    self._logger.error(f"Telegram API error: {result}")
                    context.published = False
                    context.publish_error = str(result)
            else:
                self._logger.error(
                    f"HTTP error: {response.status_code} - {response.text}"
                )
                context.published = False
                context.publish_error = f"HTTP {response.status_code}"
                
        except Exception as e:
            self._logger.exception(f"Telegram publishing failed: {e}")
            context.published = False
            context.publish_error = str(e)
            context.add_error(f"Telegram publisher failed: {e}")
        
        return context


# =============================================================================
# Multi-Publisher Component
# =============================================================================

class MultiPublisherComponent(PipelineComponent):
    """
    Компонент публикации в несколько каналов.
    
    Публикует аудио во все настроенные каналы.
    """
    
    def __init__(
        self,
        publishers: list[Publisher],
        stop_on_error: bool = False,
        enabled: bool = True,
    ):
        super().__init__(name="multi_publisher", enabled=enabled)
        self._publishers = publishers
        self._stop_on_error = stop_on_error
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.enabled:
            return self._skip(context)
        
        audio_path = context.audio_to_publish
        if audio_path is None or not audio_path.exists():
            self._logger.error("No audio to publish")
            context.add_error("MultiPublisher: no audio file available")
            return context
        
        caption = context.caption
        results = []
        
        for publisher in self._publishers:
            publisher_name = getattr(publisher, 'name', str(publisher))
            self._logger.info(f"Publishing via {publisher_name}...")
            
            try:
                success = publisher.publish(
                    audio_path=audio_path,
                    caption=caption
                )
                results.append((publisher_name, success))
                
                if success:
                    self._logger.info(f"{publisher_name}: published successfully")
                else:
                    self._logger.error(f"{publisher_name}: publish failed")
                    if self._stop_on_error:
                        break
                    
            except Exception as e:
                self._logger.error(f"{publisher_name}: exception - {e}")
                results.append((publisher_name, False))
                if self._stop_on_error:
                    break
        
        # Store results in metadata
        context.metadata["publish_results"] = results
        context.published = all(success for _, success in results)
        
        self._logger.info(
            f"Publishing complete: {sum(s for _, s in results)}/"
            f"{len(results)} successful"
        )
        
        return context
