# RSI Agent Framework

A robust, self-improving, self-healing, and self-preserving agent framework designed with security and simplicity in mind.

## Overview

This framework implements a perpetual agent system with:
- Recursive self-improvement capabilities
- Human-in-the-loop (HITL) oversight
- Secure sandbox execution
- Memory management
- Comprehensive diagnostics
- Ollama LLM integration

## Requirements

- Python 3.12+
- Docker
- Ollama (for LLM backend)
- MySQL 8.0+ (for logging)

## Quick Start

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
   - Copy `config/base_config.yaml.example` to `config/base_config.yaml`
   - Adjust settings as needed

4. Start the services:
```bash
docker-compose up -d
```

5. Run the system validator:
```bash
python tools/system_validator.py
```

6. Launch the agent:
```bash
python perpetual_llm.py
```

## Core Components

- `perpetual_llm.py`: Primary driver of the agent framework
- `rsi_module.py`: Handles recursive self-improvement
- `hitl_interface.py`: Human oversight interface
- `sandbox_executor.py`: Secure code execution with Docker isolation
- `memory_manager.py`: Persistent state management with file monitoring and versioning
- `system_task_manager.py`: Task scheduling and management
- `resilience/circuit_breaker.py`: Circuit breaker implementation for resilience

## Security Features

- Air-gapped execution environment
- Sandboxed code execution with Docker isolation
- Alternative code interpreter for lightweight execution
- HITL validation for critical changes
- Comprehensive logging and diagnostics
- Circuit breaker protection for resilience
- File integrity monitoring and versioning
- Variant simulation for security testing

## Configuration

Key configuration sections in `base_config.yaml`:
- `system`: Core system settings
- `security`: Sandbox and protection mechanisms
- `llm`: Language model settings
- `memory`: State persistence options
- `monitoring`: Health checks and metrics
- `hitl`: Human oversight settings

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Validation
```bash
python tools/verify_config.py
python tools/system_validator.py
```

## Architecture

The system follows a modular design with:
1. Core agent loop (`perpetual_agent.py`)
2. Self-improvement module (`rsi_module.py`)
3. Safety mechanisms (HITL, sandbox)
4. Memory persistence
5. Task management

## Safety Guidelines

1. Always run in a controlled environment first
2. Enable HITL interface for production
3. Review sandbox configurations
4. Monitor system logs
5. Regular backup of critical data

## Monitoring

- System metrics available on port 9090
- Logs stored in `agent-logs` volume
- MySQL logging for sandbox execution

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request
4. Ensure tests pass
5. Update documentation

## License

[Your License Here]