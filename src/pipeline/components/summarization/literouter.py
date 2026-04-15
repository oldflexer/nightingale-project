from typing import List, Dict, Any
import requests
from src.pipeline.interfaces import Summarizer

class LiteRouterSummarizer(Summarizer):
    """
    Summarizer using the LiteRouter API.
    """
    def __init__(self, api_url: str, model: str = "gemini-free"):
        self.api_url = api_url
        self.model = model

    def summarize(self, text: str, min_summary_length: int = 50) -> str:
        """
        Summarizes the given text using the LiteRouter API.

        Args:
            text: The text to summarize.
            min_summary_length: The minimum length of the summary.

        Returns:
            The summarized text.
        """
        try:
            payload = {
                "text": text,
                "model": self.model,
                "min_summary_length": min_summary_length
            }
            response = requests.post(f"{self.api_url}/summarize", json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            summary = data.get("summary", "")
            if len(summary) < min_summary_length:
                # Handle the case where the summary is too short.  Could retry, or return an error.
                return f"Summary too short: {summary}"
            return summary
        except requests.exceptions.RequestException as e:
            return f"Error during API call: {e}"
        except (ValueError, KeyError) as e:
            return f"Error parsing API response: {e}"