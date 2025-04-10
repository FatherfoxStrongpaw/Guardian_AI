import unittest
from unittest.mock import Mock, patch
import logging
from rsi_module import RSIModule

class TestRSIModule(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_memory_manager = Mock()
        self.mock_sandbox_executor = Mock()
        
        # Initialize with test config
        self.test_config = {
            "error_threshold": 0.1,
            "response_time_threshold": 0.5,
            "check_interval": 10,
            "loop_limit": 100
        }
        
        with patch('rsi_module.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = str(self.test_config)
            self.rsi = RSIModule(
                config_file="test_config.yaml",
                memory_manager_instance=self.mock_memory_manager,
                sandbox_executor=self.mock_sandbox_executor
            )

    def test_evaluate_system(self):
        """Test system evaluation metrics"""
        metrics = self.rsi.evaluate_system()
        self.assertIn('error_rate', metrics)
        self.assertIn('response_time', metrics)
        self.assertIsInstance(metrics['error_rate'], float)
        self.assertIsInstance(metrics['response_time'], float)

    def test_improvement_tasks(self):
        """Test task selection based on metrics"""
        # Test with metrics that should trigger both tasks
        metrics = {
            'error_rate': 0.2,  # Above threshold
            'response_time': 0.6  # Above threshold
        }
        tasks = self.rsi.improvement_tasks(metrics)
        self.assertEqual(len(tasks), 2)
        self.assertIn('optimize_error_handling', tasks)
        self.assertIn('optimize_response_time', tasks)

        # Test with metrics below thresholds
        metrics = {
            'error_rate': 0.05,  # Below threshold
            'response_time': 0.3  # Below threshold
        }
        tasks = self.rsi.improvement_tasks(metrics)
        self.assertEqual(len(tasks), 0)

    def test_execute_task(self):
        """Test task execution with sandbox"""
        # Setup mock sandbox response
        self.mock_sandbox_executor.run_safe.return_value = {
            "success": True,
            "output": "Task completed"
        }

        # Execute task
        self.rsi.execute_task("optimize_error_handling")
        
        # Verify sandbox was called
        self.mock_sandbox_executor.run_safe.assert_called_once()

    def test_config_loading(self):
        """Test configuration loading and validation"""
        self.assertEqual(self.rsi.config['error_threshold'], 0.1)
        self.assertEqual(self.rsi.config['response_time_threshold'], 0.5)
        self.assertEqual(self.rsi.config['loop_limit'], 100)

if __name__ == '__main__':
    unittest.main()