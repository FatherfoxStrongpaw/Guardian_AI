# Architecture Overview

## System Components

### PerpetualLLM
The main agent class that coordinates all system components and handles user interactions. It processes commands, manages the system state, and orchestrates the interaction between different modules.

### OllamaAgent
Handles communication with the Ollama API for LLM inference. Implements circuit breaker pattern to handle API failures gracefully and prevent cascading failures.

### MemoryManager
Manages persistent storage of system data, including memory records, file hashes, and execution history. Uses SQLite for structured data storage and implements circuit breaker pattern for database operations. Provides file monitoring, versioning, and change logging capabilities to protect against unauthorized modifications.

### SandboxExecutor
Provides a secure environment for executing potentially dangerous code. Uses Docker containers with resource limitations, network isolation, and enhanced security configurations to prevent security breaches. Includes code validation to block potentially dangerous operations.

### RSIModule
Implements Recursive Self-Improvement capabilities, allowing the system to analyze its own performance and make improvements. Runs in a separate thread to avoid blocking the main execution flow.

### HITLInterface
Human-In-The-Loop interface that allows human operators to review and approve critical operations. Provides a safety mechanism for potentially dangerous actions.

### CircuitBreaker
Implements the circuit breaker pattern to prevent cascading failures when external services or resources are unavailable. Automatically recovers when services become available again. Used throughout the system to enhance resilience and provide graceful degradation.

## Resilience Patterns

### Circuit Breaker
The system uses circuit breakers to protect against failures in external dependencies:
- API calls to Ollama service
- Database operations
- File system operations

When a service fails repeatedly, the circuit breaker opens and prevents further calls, using fallback mechanisms instead. After a recovery period, it allows a test call to see if the service has recovered.

### Graceful Degradation
The system is designed to continue functioning with reduced capabilities when components fail:
- Local fallbacks for API failures
- In-memory operation when database is unavailable
- Default responses when file operations fail

### Self-Healing
The RSI module monitors system health and attempts to recover from failures:
- Periodic health checks
- Automatic recovery attempts
- Resource optimization

## Data Flow

1. User input is received by PerpetualLLM
2. If input starts with '!', it's treated as a command and routed to the appropriate handler:
   - `!rsi`: Handled by handle_rsi_command
   - `!system`: Handled by handle_system_command
   - `!analyze`: Handled by handle_analysis_command
   - `!status`: Handled by get_system_status
   - `!help`: Handled by show_help
   - `!consider_self`: Handled by run_self_diagnostic
   - `!interpret`: Handled by handle_code_interpretation
3. If input starts with '!' but is not a recognized command, it's treated as a shell command and executed locally
4. For regular input (not commands), OllamaAgent generates responses with circuit breaker protection
5. Results are stored in MemoryManager with circuit breaker protection
6. System health is monitored by SystemMonitor
7. RSIModule periodically analyzes performance and makes improvements
8. MemoryManager periodically checks file integrity and maintains version history

## Security Architecture

The system implements multiple layers of security:
1. Input validation and sanitization
2. Sandboxed code execution with Docker isolation
3. Alternative code interpreter for lightweight execution
4. Resource limitations and quotas
5. Human review for critical operations
6. File integrity monitoring and versioning
7. Change logging and audit trails
8. Variant simulation for security testing

## Configuration Management

Configuration is managed through YAML files:
- base_config.yaml: Core system settings
- logging_config.yaml: Logging configuration

The ConfigManager class provides a unified interface for accessing configuration values with default fallbacks.