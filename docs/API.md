# API Documentation

## PerpetualLLM Class

### Methods

#### async process_input(user_input: str) -> Dict
Processes user input and executes appropriate action.

Parameters:
- `user_input`: The input string from the user

Returns:
- Dictionary containing:
  - `status`: "success" or "error"
  - `response`: Response text (on success)
  - `error`: Error message (on failure)

#### async handle_command(command: str) -> Dict
Handles system commands.

Parameters:
- `command`: The command string (without the leading !)

Returns:
- Dictionary containing command execution results

Supported Commands:
- `rsi`: Execute RSI-related operations
- `system`: Execute system commands (sandboxed)
- `analyze`: Analyze system output or behavior
- `status`: Show system status or specific metrics
- `help`: Show help message or specific command help
- `consider_self`: Run system self-diagnostics
- `interpret`: Execute Python code in a safe interpreter

#### async handle_code_interpretation(args: List[str]) -> Dict
Handle code interpretation requests.

Parameters:
- `args`: List of arguments, joined to form the code to execute

Returns:
- Dictionary containing:
  - `status`: "success" or "error"
  - `response`: Dictionary with output and variables (on success)
  - `error`: Error message (on failure)

#### simulate_variants(aggressive=False, passive=False, dangerous=False) -> Dict
Simulates the behavior of Aggressive, Passive, and Dangerous variants.

Parameters:
- `aggressive`: Whether to simulate aggressive variant
- `passive`: Whether to simulate passive variant
- `dangerous`: Whether to simulate dangerous variant

Returns:
- Dictionary containing simulation results

#### verify_file_integrity() -> bool
Verifies integrity of critical files with circuit breaker protection.

Returns:
- `True` if all files pass integrity check, `False` otherwise

#### async run_self_diagnostic(args: List[str] = None) -> Dict
Runs system self-diagnostics.

Parameters:
- `args`: Optional list of diagnostic types to run

Returns:
- Dictionary containing diagnostic results

## OllamaAgent Class

### Methods

#### async generate_response(prompt: str) -> str
Generate response using Ollama API with circuit breaker protection.

Parameters:
- `prompt`: The prompt to send to the model

Returns:
- Generated text response

#### async get_model_info() -> Dict
Get information about the current model with circuit breaker protection.

Returns:
- Dictionary containing model information

#### _make_api_call(prompt: str) -> str
Make the actual API call to Ollama (protected by circuit breaker).

Parameters:
- `prompt`: The prompt to send to the model

Returns:
- Generated text response

#### _api_fallback() -> str
Fallback response when circuit breaker is open.

Returns:
- Fallback message for the user

## MemoryManager Class

### Methods

#### store(key, value, type_hint="general", ttl=None)
Store a value with optional TTL using circuit breaker protection.

Parameters:
- `key`: The key to store the value under
- `value`: The value to store
- `type_hint`: Type of data being stored
- `ttl`: Time-to-live in seconds (optional)

Returns:
- `True` if successful, `False` otherwise

#### retrieve(key)
Retrieve a value, respecting TTL, with circuit breaker protection.

Parameters:
- `key`: The key to retrieve

Returns:
- The stored value or `None` if not found or expired

#### get_hash(file_path: str) -> str
Get the stored hash for a file.

Parameters:
- `file_path`: Path to the file

Returns:
- Hash string or `None` if not found

#### store_hash(file_path: str, hash_value: str)
Store a hash for a file.

Parameters:
- `file_path`: Path to the file
- `hash_value`: Hash value to store

Returns:
- `True` if successful, `False` otherwise

#### store_file_version(file_path: str, content: bytes, change_description: str = None)
Store a version of a file.

Parameters:
- `file_path`: Path to the file
- `content`: File content as bytes
- `change_description`: Optional description of changes

Returns:
- `True` if successful, `False` otherwise

#### get_file_versions(file_path: str, limit: int = 10)
Get version history for a file.

Parameters:
- `file_path`: Path to the file
- `limit`: Maximum number of versions to return

Returns:
- List of version dictionaries with id, hash, timestamp, and description

#### restore_file_version(version_id: int)
Restore a specific version of a file.

Parameters:
- `version_id`: ID of the version to restore

Returns:
- Dictionary with file_path, content, and hash if successful, `None` otherwise

#### register_monitored_file(file_path: str, is_critical: bool = False)
Register a file for monitoring.

Parameters:
- `file_path`: Path to the file
- `is_critical`: Whether the file is critical for system operation

Returns:
- `True` if successful, `False` otherwise

#### check_monitored_files()
Check all monitored files for changes.

Returns:
- List of dictionaries with file_path, status, and is_critical

#### check_file_integrity(file_path: str, is_critical: bool = False)
Check if a file has been modified.

Parameters:
- `file_path`: Path to the file
- `is_critical`: Whether the file is critical for system operation

Returns:
- Dictionary with file_path, status, and is_critical

#### add_changelog_entry(file_path: str = None, action: str = None, details: str = None, user: str = None)
Add an entry to the changelog.

Parameters:
- `file_path`: Path to the file (optional)
- `action`: Action performed (optional)
- `details`: Additional details (optional)
- `user`: User who performed the action (optional)

Returns:
- `True` if successful, `False` otherwise

#### get_changelog(limit: int = 100, file_path: str = None)
Get recent changelog entries.

Parameters:
- `limit`: Maximum number of entries to return
- `file_path`: Filter by file path (optional)

Returns:
- List of changelog entry dictionaries

## CircuitBreaker Class

### Methods

#### execute(func: Callable, *args, **kwargs) -> Any
Execute a function with circuit breaker protection.

Parameters:
- `func`: The function to execute
- `*args`, `**kwargs`: Arguments to pass to the function

Returns:
- Result of the function or fallback response if circuit is open

### States

- `CLOSED`: Normal operation, all requests pass through
- `OPEN`: Failing state, requests are short-circuited to fallback
- `HALF_OPEN`: Testing recovery, allows a single request to test if the service has recovered

## CodeInterpreter Class

### Methods

#### execute(code: str) -> Tuple[str, str, str, Dict]
Execute the given code snippet in a sandboxed subprocess.

Parameters:
- `code`: Python code to execute

Returns:
- Tuple containing:
  - `status`: "success", "error", or "timeout"
  - `output`: Captured stdout
  - `error_message`: Captured stderr or error message
  - `local_vars`: Dictionary of local variables after execution
