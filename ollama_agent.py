import json
import time
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_prompt(prompt, retry=3, timeout=30):
    """
    Sends a structured prompt to Ollama and returns the response.
    Handles unexpected failures and logs errors properly.
    """
    url = "http://127.0.0.1:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {"model": "mistral", "prompt": prompt, "stream": False}

    for attempt in range(1, retry + 1):
        try:
            logger.info(f"Sending prompt to Ollama (Attempt {attempt}): {prompt}")
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            response.raise_for_status()

            # Verify JSON format
            try:
                json_response = response.json()
            except json.JSONDecodeError:
                logger.error(f"Unexpected non-JSON response from Ollama: {response.text}")
                return {"response": None, "status": "error", "error": "Invalid JSON response from Ollama"}

            # Validate expected response format
            final_response = json_response.get("response")
            if not final_response:
                logger.warning(f"Ollama returned an empty response: {json_response}")
                return {"response": None, "status": "error", "error": "Empty response"}

            return {"response": final_response, "status": "success"}

        except requests.RequestException as e:
            logger.error(f"Request error on attempt {attempt}: {e}")
            time.sleep(1)  # Backoff before retrying
            if attempt == retry:
                return {"response": None, "status": "error", "error": str(e)}

    return {"response": None, "status": "error", "error": "Failed after retries"}

# 🔥 Now run the test AFTER the function is properly defined
if __name__ == "__main__":
    print(send_prompt("Hello, Ollama!"))
