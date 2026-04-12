import json
import time
import requests
from typing import Optional
from loguru import logger
from src.pipeline.interfaces import Summarizer


class OllamaSummarizer(Summarizer):
    def __init__(
        self,
        api_url: str,
        model: str,
        system_prompt: str,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        temperature: float = 0.5,
        max_tokens: int = 500,
    ):
        self.api_url = api_url.rstrip('/') + '/api/generate'
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self.max_tokens = max_tokens

    def summarize(self, raw_text: str) -> str:
        # Формируем промпт: системный + пользовательский текст
        full_prompt = f"{self.system_prompt}\n\nНовости:\n{raw_text}\n\n"
        
        options = {"temperature": self.temperature}
        if self.max_tokens > 0:
            options["num_predict"] = self.max_tokens
            
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": options
        }

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Ollama request attempt {attempt}/{self.max_retries}")
                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                summary = data.get("response", "").strip()
                if not summary:
                    raise ValueError("Empty response from Ollama")
                logger.info(f"Summary generated, length: {len(summary)} chars")
                logger.info(summary)
                return summary
            except Exception as e:
                logger.warning(f"Ollama request failed (attempt {attempt}): {e}")
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
        raise RuntimeError(f"Ollama summarization failed after {self.max_retries} attempts. Last error: {last_exception}")