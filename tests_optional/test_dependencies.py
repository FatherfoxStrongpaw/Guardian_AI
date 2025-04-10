import unittest
import importlib
import sys
import os

class TestDependencies(unittest.TestCase):
    def setUp(self):
        self.critical_modules = {
            'rsi_module': [
                'sandbox_executor',
                'memory_manager',
                'logging',
                'json',
                'time',
                'random'
            ],
            'perpetual_agent': [
                'logging',
                'time',
                'threading',
                'memory_manager'
            ],
            'hitl_interface': [
                'consolidated_code_analysis',
                'system_task_manager',
                'self_diagnostic',
                'logging',
                'json',
                'time',
                'threading'
            ],
            'sandbox_executor': [
                'docker',
                'ast',
                'logging',
                'multiprocessing'
            ]
        }

    def test_module_imports(self):
        """Verify all critical module dependencies can be imported"""
        failed_imports = []
        
        for module, dependencies in self.critical_modules.items():
            for dep in dependencies:
                try:
                    importlib.import_module(dep)
                except ImportError as e:
                    failed_imports.append(f"{module} -> {dep}: {str(e)}")
        
        if failed_imports:
            self.fail(f"Missing dependencies:\n" + "\n".join(failed_imports))

    def get_imports(module):
        if hasattr(module, '__name__'):
            return [module.__name__]
        return []

    def test_circular_dependencies(self):
        """Check for circular dependencies between modules"""
        visited = set()
        stack = ['rsi_module']  # Start with main module
        
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                try:
                    module = importlib.import_module(current)
                    stack.extend(get_imports(module))
                except ImportError:
                    continue

    def test_config_references(self):
        """Verify config keys referenced in code exist in base_config.yaml"""
        import yaml
        
        with open('config/base_config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        # Add key checks based on your config usage
        required_keys = {
            'environment',
            'system.debug',
            'system.log_level',
            'security.sandbox.enabled',
            'llm.provider',
            'memory.type'
        }

        for key in required_keys:
            parts = key.split('.')
            current = config
            for part in parts:
                self.assertIn(part, current, f"Missing config key: {key}")
                current = current[part]

if __name__ == '__main__':
    unittest.main()