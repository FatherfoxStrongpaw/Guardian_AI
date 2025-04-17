# Guardian AI Package Structure Improvement Plan

## Current Structure

The current structure has files scattered across the root directory and various subdirectories without a clear organizational pattern:

```
./
├── analyze_dependencies.py
├── centralized_diagnostics.py
├── code_interpreter.py
├── command_processor.py
├── consolidated_code_analysis.py
├── core/
│   └── config.py
├── final_verification.py
├── hitl_interface.py
├── main.py
├── memory/
│   └── memory_manager.py
├── memory_manager.py
├── monitoring/
│   ├── health_checker.py
│   └── metrics_collector.py
├── ollama_agent.py
├── perpetual_agent_old.py
├── perpetual_llm.py
├── recovery/
│   └── system_recovery.py
├── resilience/
│   └── circuit_breaker.py
├── rsi_module.py
├── run_guardian.py
├── run_tests.py
├── sandbox_excecuter.py
├── sandbox_executor.py
├── self_diagnostic.py
├── system_task_manager.py
├── test_rsi_module.py
├── tests/
│   ├── test_integration.py
│   ├── test_memory_manager.py
│   ├── test_rsi_module.py
│   └── test_sandbox_executor.py
├── tests_optional/
│   ├── test_circular_deps.py
│   ├── test_consolidated_code_analysis.py
│   ├── test_dependencies.py
│   ├── test_hitl_interface.py
│   └── test_security.py
├── tools/
│   ├── system_validator.py
│   ├── verify_config.py
│   └── verify_dependencies.py
├── validation/
│   └── directive_validator.py
└── verify_dependencies.py
```

## Proposed Structure

The proposed structure organizes the codebase into a proper Python package with clear separation of concerns:

```
guardian_ai/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── perpetual_llm.py
│   ├── rsi_module.py
│   └── system_task_manager.py
├── memory/
│   ├── __init__.py
│   └── memory_manager.py
├── security/
│   ├── __init__.py
│   ├── sandbox_executor.py
│   └── directive_validator.py
├── resilience/
│   ├── __init__.py
│   └── circuit_breaker.py
├── monitoring/
│   ├── __init__.py
│   ├── health_checker.py
│   └── metrics_collector.py
├── recovery/
│   ├── __init__.py
│   └── system_recovery.py
├── interface/
│   ├── __init__.py
│   ├── hitl_interface.py
│   └── ollama_agent.py
├── tools/
│   ├── __init__.py
│   ├── system_validator.py
│   ├── verify_config.py
│   └── verify_dependencies.py
├── analysis/
│   ├── __init__.py
│   ├── analyze_dependencies.py
│   ├── consolidated_code_analysis.py
│   └── self_diagnostic.py
├── tests/
│   ├── __init__.py
│   ├── test_integration.py
│   ├── test_memory_manager.py
│   ├── test_rsi_module.py
│   └── test_sandbox_executor.py
└── tests_optional/
    ├── __init__.py
    ├── test_circular_deps.py
    ├── test_consolidated_code_analysis.py
    ├── test_dependencies.py
    ├── test_hitl_interface.py
    └── test_security.py
```

## Migration Plan

### Phase 1: Create Package Structure

1. Create the guardian_ai directory
2. Create __init__.py files in each subdirectory
3. Create setup.py for package installation

### Phase 2: Move Files to New Structure

#### Core Module
- Move perpetual_llm.py to guardian_ai/core/
- Move rsi_module.py to guardian_ai/core/
- Move system_task_manager.py to guardian_ai/core/
- Move core/config.py to guardian_ai/core/

#### Memory Module
- Move memory_manager.py to guardian_ai/memory/
- Remove memory/memory_manager.py after integration

#### Security Module
- Move sandbox_executor.py to guardian_ai/security/
- Move validation/directive_validator.py to guardian_ai/security/
- Remove sandbox_excecuter.py after integration

#### Resilience Module
- Move resilience/circuit_breaker.py to guardian_ai/resilience/

#### Monitoring Module
- Move monitoring/health_checker.py to guardian_ai/monitoring/
- Move monitoring/metrics_collector.py to guardian_ai/monitoring/

#### Recovery Module
- Move recovery/system_recovery.py to guardian_ai/recovery/

#### Interface Module
- Move hitl_interface.py to guardian_ai/interface/
- Move ollama_agent.py to guardian_ai/interface/

#### Tools Module
- Move tools/system_validator.py to guardian_ai/tools/
- Move tools/verify_config.py to guardian_ai/tools/
- Move tools/verify_dependencies.py to guardian_ai/tools/
- Remove verify_dependencies.py after integration

#### Analysis Module
- Move analyze_dependencies.py to guardian_ai/analysis/
- Move consolidated_code_analysis.py to guardian_ai/analysis/
- Move self_diagnostic.py to guardian_ai/analysis/
- Move centralized_diagnostics.py to guardian_ai/analysis/
- Move final_verification.py to guardian_ai/analysis/

#### Tests
- Move tests/ to guardian_ai/tests/
- Move tests_optional/ to guardian_ai/tests_optional/
- Remove test_rsi_module.py after integration

### Phase 3: Update Imports

#### Update Relative Imports
Update all import statements to use the new package structure:

```python
# Old imports
from memory_manager import MemoryManager
from sandbox_executor import SandboxExecutor
from perpetual_llm import PerpetualLLM
from resilience.circuit_breaker import CircuitBreaker

# New imports
from guardian_ai.memory.memory_manager import MemoryManager
from guardian_ai.security.sandbox_executor import SandboxExecutor
from guardian_ai.core.perpetual_llm import PerpetualLLM
from guardian_ai.resilience.circuit_breaker import CircuitBreaker
```

#### Create Compatibility Layer
Create compatibility modules in the root directory for backward compatibility:

```python
# memory_manager.py in root directory
import warnings
warnings.warn("This module is deprecated, use guardian_ai.memory.memory_manager instead", DeprecationWarning)
from guardian_ai.memory.memory_manager import *
```

### Phase 4: Update Entry Points

#### Update Main Entry Point
Create a new main.py in the guardian_ai directory:

```python
# guardian_ai/main.py
from guardian_ai.core.perpetual_llm import PerpetualLLM
from guardian_ai.memory.memory_manager import MemoryManager
from guardian_ai.core.rsi_module import RSIModule
from guardian_ai.security.sandbox_executor import SandboxExecutor
from guardian_ai.core.config import ConfigManager

# Rest of main.py code...
```

#### Update Run Scripts
Update run_guardian.py and run_tests.py to use the new package structure.

### Phase 5: Testing

1. Run all tests to verify functionality
2. Fix any import issues
3. Verify all components work together

### Phase 6: Documentation

1. Update all documentation to reflect the new package structure
2. Create migration guide for users
3. Update README.md with installation instructions

## Backward Compatibility

To ensure backward compatibility during the transition:

1. Create compatibility modules in the root directory
2. Use deprecation warnings to notify users
3. Maintain compatibility for at least 2-3 release cycles

## Timeline

### Week 1: Create Package Structure
- Create guardian_ai directory
- Create __init__.py files
- Create setup.py

### Week 2-3: Move Files and Update Imports
- Move files to new structure
- Update import statements
- Create compatibility layers

### Week 4: Testing and Fixing
- Run all tests
- Fix any issues
- Verify functionality

### Week 5: Documentation and Finalization
- Update documentation
- Create migration guide
- Finalize package structure
