# Duplicate Files Integration Plan

This document provides a detailed plan for integrating functionality from duplicate files while ensuring no functionality is lost.

## memory_manager.py vs memory/memory_manager.py

### Similarity Analysis
- **Similarity**: 4.95%
- **Primary File**: memory_manager.py
- **Secondary File**: memory/memory_manager.py

### Unique Functions in memory_manager.py
- get_hash
- store_hash
- get_status
- _db_operation_fallback
- connection
- _execute_store
- _execute_retrieve
- _compute_checksum
- atomic_write
- load_memory
- save_memory
- add_record
- get_records
- rollback_last
- store_file_version
- get_file_versions
- restore_file_version
- register_monitored_file
- check_monitored_files
- check_file_integrity
- add_changelog_entry
- get_changelog

### Unique Functions in memory/memory_manager.py
- log_execution
- get_execution_history

### Integration Plan
1. **Keep memory_manager.py as the primary file**
2. **Add the following functions from memory/memory_manager.py**:
   - log_execution
   - get_execution_history
3. **Database Schema Updates**:
   - Add execution_history table if not already present
4. **Compatibility Layer**:
   ```python
   # In memory/memory_manager.py
   import warnings
   warnings.warn("memory.memory_manager is deprecated, use memory_manager instead", DeprecationWarning)
   from memory_manager import MemoryManager, log_execution, get_execution_history
   ```
5. **Testing**:
   - Test log_execution functionality
   - Test get_execution_history functionality
   - Verify existing functionality still works

## sandbox_executor.py vs sandbox_excecuter.py

### Similarity Analysis
- **Similarity**: 23.49%
- **Primary File**: sandbox_executor.py
- **Secondary File**: sandbox_excecuter.py

### Unique Functions in sandbox_executor.py
- validate_code
- execute

### Unique Features in sandbox_excecuter.py
- MySQL connector integration
- Different security configurations

### Integration Plan
1. **Keep sandbox_executor.py as the primary file**
2. **Add MySQL connector integration from sandbox_excecuter.py**:
   - Add MySQL connection handling
   - Add MySQL-specific error handling
3. **Ensure security configurations are preserved**:
   - Verify all security settings from sandbox_excecuter.py are included
4. **Compatibility Layer**:
   ```python
   # In sandbox_excecuter.py
   import warnings
   warnings.warn("sandbox_excecuter is deprecated, use sandbox_executor instead", DeprecationWarning)
   from sandbox_executor import SandboxExecutor
   ```
5. **Testing**:
   - Test MySQL connector functionality
   - Verify security configurations work as expected
   - Verify existing functionality still works

## verify_dependencies.py vs tools/verify_dependencies.py

### Similarity Analysis
- **Similarity**: 10.14%
- **Primary File**: tools/verify_dependencies.py
- **Secondary File**: verify_dependencies.py

### Unique Functions in verify_dependencies.py
- verify_imports
- verify_file_exists
- main

### Unique Functions in tools/verify_dependencies.py
- verify_module_dependencies

### Integration Plan
1. **Keep tools/verify_dependencies.py as the primary file**
2. **Add the following functions from verify_dependencies.py**:
   - verify_imports
   - verify_file_exists
   - Integrate main function logic
3. **Ensure command-line interface compatibility**:
   - Preserve all command-line arguments
4. **Compatibility Layer**:
   ```python
   # In verify_dependencies.py
   import warnings
   warnings.warn("verify_dependencies is deprecated, use tools.verify_dependencies instead", DeprecationWarning)
   from tools.verify_dependencies import verify_module_dependencies, verify_imports, verify_file_exists
   ```
5. **Testing**:
   - Test verify_imports functionality
   - Test verify_file_exists functionality
   - Verify command-line interface works as expected

## perpetual_llm.py vs perpetual_agent_old.py

### Similarity Analysis
- **Primary File**: perpetual_llm.py
- **Secondary File**: perpetual_agent_old.py

### Key Features to Verify in perpetual_llm.py
- Variant simulation
- CLI interface
- Priority layers and weights
- Variant performance tracking

### Integration Plan
1. **Keep perpetual_llm.py as the primary file**
2. **Verify all variant simulation functionality is integrated**:
   - Check simulate_variants method
   - Verify priority layers and weights
   - Verify variant performance tracking
3. **Check for any unique CLI features in perpetual_agent_old.py**:
   - Identify any missing CLI commands
   - Integrate any missing functionality
4. **Compatibility Layer**:
   ```python
   # In perpetual_agent_old.py
   import warnings
   warnings.warn("perpetual_agent_old is deprecated, use perpetual_llm instead", DeprecationWarning)
   from perpetual_llm import PerpetualLLM
   ```
5. **Testing**:
   - Test variant simulation functionality
   - Test CLI interface
   - Verify existing functionality still works

## test_rsi_module.py vs tests/test_rsi_module.py

### Similarity Analysis
- **Similarity**: 16.97%
- **Primary File**: tests/test_rsi_module.py
- **Secondary File**: test_rsi_module.py

### Unique Functions in test_rsi_module.py
- tearDown
- test_load_config
- test_execute_task_updates_config
- test_run_loop_safeguard
- test_circuit_breaker_recovery
- test_degraded_mode_operation

### Unique Functions in tests/test_rsi_module.py
- test_evaluate_system
- test_execute_task
- test_config_loading

### Integration Plan
1. **Keep tests/test_rsi_module.py as the primary file**
2. **Add the following test methods from test_rsi_module.py**:
   - tearDown
   - test_load_config
   - test_execute_task_updates_config
   - test_run_loop_safeguard
   - test_circuit_breaker_recovery
   - test_degraded_mode_operation
3. **Ensure setUp method is compatible with all tests**
4. **Testing**:
   - Run all tests to verify they pass
   - Check for any conflicts between test methods

## Implementation Timeline

### Week 1: Analysis and Planning
- Complete function-by-function analysis
- Create detailed integration plans
- Set up testing infrastructure

### Week 2: memory_manager.py Integration
- Integrate functionality from memory/memory_manager.py
- Add compatibility layer
- Run tests and fix issues

### Week 3: sandbox_executor.py Integration
- Integrate MySQL connector functionality
- Ensure security configurations are preserved
- Run tests and fix issues

### Week 4: tools/verify_dependencies.py Integration
- Integrate functionality from verify_dependencies.py
- Ensure command-line interface compatibility
- Run tests and fix issues

### Week 5: perpetual_llm.py Verification
- Verify all variant simulation functionality
- Integrate any missing CLI features
- Run tests and fix issues

### Week 6: tests/test_rsi_module.py Integration
- Integrate test methods from test_rsi_module.py
- Run tests and fix issues

### Week 7: Monitoring and Fixing
- Monitor for any issues
- Fix problems as they arise
- Update documentation

### Week 8: Cleanup
- Remove deprecated files
- Remove compatibility layers
- Finalize documentation
