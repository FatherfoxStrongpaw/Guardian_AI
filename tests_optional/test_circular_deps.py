import unittest
import importlib
import sys
from pathlib import Path

class TestCircularDependencies(unittest.TestCase):
    def setUp(self):
        self.modules = {
            'rsi_module': ['perpetual_agent', 'memory_manager', 'sandbox_executor'],
            'hitl_interface': ['system_task_manager', 'consolidated_code_analysis'],
            'perpetual_agent': ['memory_manager'],
            'sandbox_executor': ['memory_manager'],
            'memory_manager': [],
            'consolidated_code_analysis': ['memory_manager']
        }

    def test_no_circular_dependencies(self):
        def check_circular(module, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if module in path:
                return False, path + [module]
            
            if module in visited:
                return True, path
            
            visited.add(module)
            path.append(module)
            
            for dep in self.modules.get(module, []):
                ok, circular_path = check_circular(dep, visited, path[:])
                if not ok:
                    return False, circular_path
            
            return True, path

        for module in self.modules:
            ok, path = check_circular(module)
            self.assertTrue(ok, f"Circular dependency detected: {' -> '.join(path)}")

if __name__ == '__main__':
    unittest.main()