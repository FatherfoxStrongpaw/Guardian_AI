import logging
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class SystemValidator:
    def __init__(self):
        self.required_modules = [
            'rsi_module',
            'perpetual_agent',
            'sandbox_executor',
            'memory_manager',
            'hitl_interface',
            'consolidated_code_analysis',
            'system_task_manager'
        ]
        
        self.required_configs = {
            'system': ['debug', 'log_level', 'max_retries'],
            'security.sandbox': ['enabled', 'timeout', 'max_memory'],
            'llm': ['provider', 'model', 'temperature'],
            'memory': ['type', 'path']
        }

    def validate_system(self) -> Tuple[bool, List[str]]:
        """Enhanced system validation including circular dependency check"""
        errors = []
        
        # Existing validation
        for module_name in self.required_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                errors.append(f"Failed to import {module_name}: {str(e)}")

        # Add circular dependency check
        circular_deps = self.check_circular_dependencies()
        errors.extend(circular_deps)
        
        # Existing interface and config validation
        errors.extend(self.validate_module_interfaces())
        errors.extend(self.validate_configurations())
        
        return len(errors) == 0, errors

    def validate_module_interfaces(self) -> List[str]:
        """Validate that all required modules implement necessary interfaces"""
        errors = []
        
        # Check RSIModule interface
        try:
            from rsi_module import RSIModule
            required_methods = ['evaluate_system', 'execute_task', 'improvement_tasks']
            for method in required_methods:
                if not hasattr(RSIModule, method):
                    errors.append(f"RSIModule missing required method: {method}")
        except Exception as e:
            errors.append(f"Failed to validate RSIModule interface: {str(e)}")

        return errors

    def validate_configurations(self) -> List[str]:
        """Validate configuration files and their contents"""
        errors = []
        
        try:
            import yaml
            with open('config/base_config.yaml', 'r') as f:
                config = yaml.safe_load(f)
                
            # Check required configuration keys
            for section, keys in self.required_configs.items():
                section_parts = section.split('.')
                current = config
                for part in section_parts:
                    if part not in current:
                        errors.append(f"Missing configuration section: {section}")
                        break
                    current = current[part]
                
                if isinstance(current, dict):
                    for key in keys:
                        if key not in current:
                            errors.append(f"Missing configuration key: {section}.{key}")
                            
        except Exception as e:
            errors.append(f"Configuration validation failed: {str(e)}")
            
        return errors

    def check_circular_dependencies(self) -> List[str]:
        """Check for circular dependencies between modules"""
        errors = []
        dependency_graph = {}
        
        def build_dependency_graph(module_name: str, visited: set):
            if module_name in visited:
                errors.append(f"Circular dependency detected: {' -> '.join(visited)} -> {module_name}")
                return
            
            visited.add(module_name)
            try:
                module = importlib.import_module(module_name)
                for name, obj in module.__dict__.items():
                    if hasattr(obj, '__module__') and obj.__module__ not in visited:
                        build_dependency_graph(obj.__module__, visited.copy())
            except ImportError as e:
                errors.append(f"Failed to import {module_name} while checking dependencies: {str(e)}")
                
        for module in self.required_modules:
            build_dependency_graph(module, set())
        
        return errors

def main():
    logging.basicConfig(level=logging.INFO)
    validator = SystemValidator()
    success, errors = validator.validate_system()
    
    if success:
        logger.info("System validation completed successfully!")
    else:
        logger.error("System validation failed!")
        for error in errors:
            logger.error(f"- {error}")
        sys.exit(1)

if __name__ == '__main__':
    main()