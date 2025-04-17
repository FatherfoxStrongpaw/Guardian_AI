# Import Standardization Plan

## Current Issues

The codebase currently has several issues with imports:

1. **Inconsistent Import Styles**: Different files use different import styles
2. **Duplicate Files**: Some files import from duplicate modules
3. **No Clear Organization**: Imports are not consistently grouped or ordered
4. **Relative vs Absolute Imports**: Mix of relative and absolute imports

## Import Style Guide

### Import Grouping

All imports should be grouped into three sections, separated by a blank line:

1. **Standard Library Imports**
2. **Third-Party Library Imports**
3. **Local/Project Imports**

Example:
```python
# Standard library imports
import os
import sys
import logging
from typing import Dict, List, Optional

# Third-party library imports
import yaml
import docker
import requests

# Local/project imports
from guardian_ai.core.config import ConfigManager
from guardian_ai.memory.memory_manager import MemoryManager
from guardian_ai.resilience.circuit_breaker import CircuitBreaker
```

### Import Order

Within each group, imports should be alphabetically ordered:

```python
# Correct
import json
import os
import sys

# Incorrect
import sys
import os
import json
```

### Import Style

For consistency, use the following import styles:

1. **For Standard Library Modules**:
   ```python
   import os
   import sys
   from datetime import datetime
   ```

2. **For Third-Party Libraries**:
   ```python
   import yaml
   import docker
   from requests import Session
   ```

3. **For Local/Project Modules**:
   ```python
   from guardian_ai.core.config import ConfigManager
   from guardian_ai.memory.memory_manager import MemoryManager
   ```

4. **For Multiple Imports from Same Module**:
   ```python
   from typing import Dict, List, Optional, Union
   ```

### Absolute vs Relative Imports

Use absolute imports for clarity and maintainability:

```python
# Preferred (absolute import)
from guardian_ai.memory.memory_manager import MemoryManager

# Avoid (relative import)
from ..memory.memory_manager import MemoryManager
```

## Implementation Plan

### Phase 1: Identify Files to Update

1. Scan all Python files in the codebase
2. Identify files with non-standard import patterns
3. Prioritize files with duplicate imports

### Phase 2: Update Imports for Duplicate Files

Update imports for files that import from duplicate modules:

1. **memory_manager.py vs memory/memory_manager.py**:
   - Update all imports to use `from guardian_ai.memory.memory_manager import MemoryManager`

2. **sandbox_executor.py vs sandbox_excecuter.py**:
   - Update all imports to use `from guardian_ai.security.sandbox_executor import SandboxExecutor`

3. **verify_dependencies.py vs tools/verify_dependencies.py**:
   - Update all imports to use `from guardian_ai.tools.verify_dependencies import verify_module_dependencies`

4. **perpetual_llm.py vs perpetual_agent_old.py**:
   - Update all imports to use `from guardian_ai.core.perpetual_llm import PerpetualLLM`

### Phase 3: Standardize Import Style

For each file in the codebase:

1. Identify all import statements
2. Group imports into standard library, third-party, and local
3. Alphabetically order imports within each group
4. Update import styles to match the style guide
5. Convert relative imports to absolute imports

### Phase 4: Create Import Linting Rules

1. Set up linting rules for import style
2. Add import checks to CI/CD pipeline
3. Create pre-commit hooks for import validation

## Files to Update

The following files need import standardization:

### Core Files
- [ ] perpetual_llm.py
- [ ] rsi_module.py
- [ ] system_task_manager.py
- [ ] main.py

### Memory Management
- [ ] memory_manager.py
- [ ] memory/memory_manager.py

### Security
- [ ] sandbox_executor.py
- [ ] sandbox_excecuter.py
- [ ] validation/directive_validator.py

### Resilience
- [ ] resilience/circuit_breaker.py

### Monitoring
- [ ] monitoring/health_checker.py
- [ ] monitoring/metrics_collector.py

### Recovery
- [ ] recovery/system_recovery.py

### Interface
- [ ] hitl_interface.py
- [ ] ollama_agent.py

### Tools
- [ ] tools/system_validator.py
- [ ] tools/verify_config.py
- [ ] tools/verify_dependencies.py
- [ ] verify_dependencies.py

### Analysis
- [ ] analyze_dependencies.py
- [ ] consolidated_code_analysis.py
- [ ] self_diagnostic.py
- [ ] centralized_diagnostics.py
- [ ] final_verification.py

### Tests
- [ ] tests/test_integration.py
- [ ] tests/test_memory_manager.py
- [ ] tests/test_rsi_module.py
- [ ] tests/test_sandbox_executor.py
- [ ] test_rsi_module.py
- [ ] tests_optional/test_circular_deps.py
- [ ] tests_optional/test_consolidated_code_analysis.py
- [ ] tests_optional/test_dependencies.py
- [ ] tests_optional/test_hitl_interface.py
- [ ] tests_optional/test_security.py

## Example Transformations

### Example 1: Unorganized Imports

Before:
```python
import time
from typing import Dict, List
import logging
from memory_manager import MemoryManager
import os
import yaml
from resilience.circuit_breaker import CircuitBreaker
```

After:
```python
# Standard library imports
import logging
import os
import time
from typing import Dict, List

# Third-party library imports
import yaml

# Local/project imports
from guardian_ai.memory.memory_manager import MemoryManager
from guardian_ai.resilience.circuit_breaker import CircuitBreaker
```

### Example 2: Duplicate Module Imports

Before:
```python
from memory.memory_manager import log_execution
import time
from sandbox_excecuter import SandboxExecutor
```

After:
```python
# Standard library imports
import time

# Local/project imports
from guardian_ai.memory.memory_manager import log_execution
from guardian_ai.security.sandbox_executor import SandboxExecutor
```

### Example 3: Relative Imports

Before:
```python
from ..memory.memory_manager import MemoryManager
from .config import ConfigManager
```

After:
```python
# Local/project imports
from guardian_ai.core.config import ConfigManager
from guardian_ai.memory.memory_manager import MemoryManager
```

## Timeline

### Week 1: Analysis
- Scan all Python files
- Identify non-standard import patterns
- Create detailed update plan

### Week 2: Update Duplicate File Imports
- Update imports for memory_manager.py
- Update imports for sandbox_executor.py
- Update imports for verify_dependencies.py
- Update imports for perpetual_llm.py

### Week 3-4: Standardize All Imports
- Update core files
- Update memory management files
- Update security files
- Update resilience files
- Update monitoring files
- Update recovery files
- Update interface files
- Update tools files
- Update analysis files
- Update test files

### Week 5: Testing and Linting
- Set up import linting rules
- Add import checks to CI/CD
- Create pre-commit hooks
- Test all changes

## Conclusion

Standardizing imports across the codebase will improve readability, maintainability, and reduce the likelihood of import-related errors. By following a consistent import style and using absolute imports, the codebase will be more robust and easier to navigate.
