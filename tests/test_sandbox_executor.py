import unittest
from unittest.mock import Mock, patch
import docker
from sandbox_executor import SandboxExecutor

class TestSandboxExecutor(unittest.TestCase):
    def setUp(self):
        self.config = {
            "security": {
                "sandbox": {
                    "enabled": True,
                    "timeout": 10,
                    "max_memory": "512m",
                    "allowed_modules": ["math", "time", "json"],
                    "docker": {
                        "image": "python:3.9-slim",
                        "network": "none"
                    }
                }
            }
        }
        self.executor = SandboxExecutor(self.config)

    def test_code_validation(self):
        """Test code validation before execution"""
        # Valid code
        valid_code = "result = 1 + 1"
        self.assertTrue(self.executor.validate_code(valid_code))

        # Invalid code (importing restricted module)
        invalid_code = "import os; os.system('rm -rf /')"
        self.assertFalse(self.executor.validate_code(invalid_code))

        # Invalid code (syntax error)
        invalid_syntax = "def broken_func(:"
        self.assertFalse(self.executor.validate_code(invalid_syntax))

    def test_resource_limits(self):
        """Test resource limitation enforcement"""
        # Test memory limit
        memory_heavy_code = "x = ' ' * (1024 * 1024 * 1024)"  # 1GB
        result = self.executor.execute(memory_heavy_code)
        self.assertFalse(result["success"])
        self.assertIn("memory", result["error"].lower())

        # Test timeout
        infinite_loop = "while True: pass"
        result = self.executor.execute(infinite_loop)
        self.assertFalse(result["success"])
        self.assertIn("timeout", result["error"].lower())

    @patch('docker.from_env')
    def test_container_isolation(self, mock_docker):
        """Test Docker container isolation"""
        mock_container = Mock()
        mock_docker.return_value.containers.run.return_value = mock_container

        test_code = "print('hello')"
        self.executor.execute(test_code)

        # Verify container configuration
        mock_docker.return_value.containers.run.assert_called_with(
            image=self.config["security"]["sandbox"]["docker"]["image"],
            command=["python", "-c", test_code],
            remove=True,
            network_mode="none",
            mem_limit=self.config["security"]["sandbox"]["max_memory"],
            timeout=self.config["security"]["sandbox"]["timeout"]
        )

    def test_execution_results(self):
        """Test execution result handling"""
        # Successful execution
        success_code = "result = 2 + 2"
        result = self.executor.execute(success_code)
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "4")

        # Failed execution
        failed_code = "undefined_variable"
        result = self.executor.execute(failed_code)
        self.assertFalse(result["success"])
        self.assertIn("NameError", result["error"])

    def test_module_restrictions(self):
        """Test module import restrictions"""
        for module in ["math", "time", "json"]:
            code = f"import {module}"
            result = self.executor.execute(code)
            self.assertTrue(result["success"], f"Failed to import allowed module {module}")

        restricted_modules = ["os", "sys", "subprocess"]
        for module in restricted_modules:
            code = f"import {module}"
            result = self.executor.execute(code)
            self.assertFalse(result["success"], f"Successfully imported restricted module {module}")

    def test_cleanup_handling(self):
        """Test cleanup after execution"""
        with patch.object(self.executor, '_cleanup_container') as mock_cleanup:
            self.executor.execute("print('test')")
            mock_cleanup.assert_called_once()

if __name__ == '__main__':
    unittest.main()