import requests
from typing import Any
from loguru import logger
from src.pipeline.interfaces import Summarizer
from src.pipeline.utils import retry_with_backoff


class OllamaSummarizer(Summarizer):
    """Ollama-based text summarizer with retry support."""

    # Minimum acceptable summary length in characters
    MIN_SUMMARY_LENGTH = 30

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
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _make_request(self, payload: dict[str, Any]) -> str:
        """Make a single request to Ollama API."""
        # Try /api/chat first (for modern models)
        endpoint = self.api_url + '/api/chat'
        logger.debug(f"Ollama request: {payload['model']} @ {endpoint}")

        response = requests.post(
            endpoint,
            json=payload,
            timeout=self.timeout
        )
        
        # Log HTTP status
        logger.debug(f"Ollama HTTP status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        
        # Log raw response structure for debugging
        logger.debug(f"Ollama response keys: {list(data.keys())}")
        logger.debug(f"Ollama response content (first 500 chars): {str(data)[:500]}")
        
        # Log key metrics
        done_reason = data.get("done_reason", "unknown")
        eval_count = data.get("eval_count", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        total_duration = data.get("total_duration", 0)
        logger.debug(
            f"Ollama stats: prompt_tokens={prompt_eval_count}, "
            f"eval_tokens={eval_count}, done_reason={done_reason}, "
            f"duration={total_duration / 1e9:.1f}s"
        )

        # Extract content - handle both /api/chat and thinking models
        # /api/chat returns: {"message": {"role": "assistant", "content": "..."}}
        # Thinking models put content in 'thinking' field instead
        message = data.get("message", {})
        
        content = ""
        if isinstance(message, dict):
            # Primary: content field (normal models)
            content = message.get("content", "") or ""
            # Fallback: thinking field (thinking-enabled models like DeepSeek, MiniMax)
            if not content:
                thinking = message.get("thinking", "") or ""
                if thinking:
                    logger.debug(f"Content is empty, extracting from thinking field ({len(thinking)} chars)")
                    content = thinking
        
        # Also try /api/generate format as fallback
        if not content:
            content = data.get("response", "") or ""
        if not content:
            content = data.get("content", "") or ""

        # Strip and validate
        if isinstance(content, str):
            content = content.strip()

        logger.debug(f"Ollama extracted content ({len(content)} chars): {content[:200]}...")

        # If still empty, raise with helpful message
        if not content or not isinstance(content, str):
            model_status = "unknown"
            try:
                models_response = requests.get(
                    self.api_url + '/api/tags',
                    timeout=5
                )
                if models_response.ok:
                    available_models = models_response.json().get("models", [])
                    model_status = [m.get("name", "unknown") for m in available_models]
            except Exception:
                model_status = "could not determine"
            
            raise ValueError(
                f"Empty or invalid response from Ollama. "
                f"Available models on server: {model_status}. "
                f"Requested model: '{self.model}'. "
                f"Response data: {data}"
            )
        
        # Validate minimum summary length
        if len(content) < self.MIN_SUMMARY_LENGTH:
            logger.warning(
                f"Summary too short ({len(content)} chars < {self.MIN_SUMMARY_LENGTH} min). "
                f"done_reason={done_reason}, eval_count={eval_count}. "
                f"Content preview: '{content[:100]}'"
            )
            raise ValueError(
                f"Summary too short ({len(content)} chars). "
                f"done_reason={done_reason}, eval_count={eval_count}. "
                f"Content: '{content[:100]}'"
            )

        return content

    def summarize(self, raw_text: str) -> str:
        """Summarize text using Ollama LLM with retry support."""
        options: dict[str, Any] = {"temperature": self.temperature}
        if self.max_tokens > 0:
            options["num_predict"] = self.max_tokens
            
        # Use chat format with messages — works correctly
        # with DeepSeek thinking models via /api/chat
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Новости:\n{raw_text}"},
            ],
            "stream": False,
            "options": options
        }

        logger.info(f"Summarizing text ({len(raw_text)} chars) with Ollama...")

        summary = retry_with_backoff(
            self._make_request,
            payload,
            max_retries=self.max_retries,
            base_delay=self.retry_delay,
            backoff_factor=2.0,
            exceptions=(requests.RequestException, ValueError),
        )

        logger.info(f"Summary generated, length: {len(summary)} chars")
        logger.info(summary)
        return summary