import unittest
import importlib

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
            'perpetual_llm': [
                'logging',
                'time',
                'threading',
                'memory_manager',
                'resilience.circuit_breaker'
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
            ],
            'resilience.circuit_breaker': [
                'logging',
                'time',
                'enum'
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

    def test_circular_dependencies(self):
        """Check for circular dependencies between modules"""
        # This test is redundant with test_circular_deps.py
        # Just verify that the main modules can be imported without circular dependency errors
        for module_name in self.critical_modules.keys():
            try:
                importlib.import_module(module_name.replace('resilience.', ''))
            except ImportError as e:
                if 'circular import' in str(e).lower():
                    self.fail(f"Circular import detected in {module_name}: {e}")

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
            'memory.type',
            'resilience.circuit_breaker.enabled',
            'resilience.circuit_breaker.failure_threshold',
            'resilience.circuit_breaker.recovery_timeout'
        }

        for key in required_keys:
            parts = key.split('.')
            current = config
            for part in parts:
                self.assertIn(part, current, f"Missing config key: {key}")
                current = current[part]

if __name__ == '__main__':
    unittest.main()