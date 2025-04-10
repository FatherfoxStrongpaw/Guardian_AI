# API Documentation

## OllamaAgent Class

### Methods

#### list_available_models()
Fetches list of available models from Ollama server.

Returns:
- Dictionary containing:
  - `status`: "success" or "error"
  - `models`: List of model names (on success)
  - `error`: Error message (on failure)

#### handle_system(content: str)
Handles system commands including model listing.

Commands:
- `!models`: Lists all available Ollama models
- `!help`: Shows command help
- `!consider_self`: Runs diagnostics
- `!analyze`: Analyzes input
- `!rsi`: Processes RSI directives
