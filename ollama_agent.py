import logging
import requests
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OllamaAgent:
    def __init__(self, model: str = "gemma3:12b", base_url: str = "http://localhost:11434"):
        """Initialize Ollama agent"""
        self.model = model
        self.base_url = base_url.rstrip('/')
        logger.info(f"Initialized Ollama agent with model: {model}")

    async def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False  # Disable streaming for simpler handling
                },
                stream=False
            )
            response.raise_for_status()
            
            # Parse the response and extract the generated text
            response_json = response.json()
            return response_json.get('response', '')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return f"Error generating response: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return f"Error parsing response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Unexpected error: {str(e)}"

    async def get_model_info(self) -> Dict:
        """Get information about the current model"""
        try:
            response = requests.get(f"{self.base_url}/api/show/{self.model}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}