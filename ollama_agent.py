import logging
import requests
import json
import time
from typing import Dict, Optional
from resilience.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class OllamaAgent:
    def __init__(self, model: str = "gemma3:12b", base_url: str = "http://localhost:11434",
                 failure_threshold: int = 3, recovery_timeout: int = 60):
        """Initialize Ollama agent"""
        self.model = model
        self.base_url = base_url.rstrip('/')

        # Initialize circuit breaker for API calls
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            fallback=self._api_fallback
        )

        logger.info(f"Initialized Ollama agent with model: {model}")

    def _api_fallback(self) -> str:
        """Fallback response when circuit breaker is open"""
        logger.warning("Circuit breaker is open, using fallback response")
        return "I'm currently experiencing technical difficulties. Please try again later."

    def _make_api_call(self, prompt: str) -> str:
        """Make the actual API call to Ollama"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False  # Disable streaming for simpler handling
            },
            stream=False,
            timeout=30  # Add timeout to prevent hanging
        )
        response.raise_for_status()

        # Parse the response and extract the generated text
        response_json = response.json()
        return response_json.get('response', '')

    async def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama API with circuit breaker protection"""
        try:
            # Use circuit breaker to protect against API failures
            return self.circuit_breaker.execute(
                self._make_api_call,
                prompt
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return f"Error generating response: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return f"Error parsing response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Unexpected error: {str(e)}"

    def _get_model_info_call(self) -> Dict:
        """Make the actual API call to get model info"""
        response = requests.get(
            f"{self.base_url}/api/show/{self.model}",
            timeout=30  # Add timeout to prevent hanging
        )
        response.raise_for_status()
        return response.json()

    def _model_info_fallback(self) -> Dict:
        """Fallback when circuit breaker is open for model info"""
        logger.warning("Circuit breaker is open for model info, using fallback")
        return {"status": "unavailable", "message": "Model information temporarily unavailable"}

    async def get_model_info(self) -> Dict:
        """Get information about the current model with circuit breaker protection"""
        try:
            # Use circuit breaker to protect against API failures
            return self.circuit_breaker.execute(self._get_model_info_call)
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}