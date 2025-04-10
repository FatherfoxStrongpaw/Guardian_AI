import unittest
import os
import json
import time
from rsi_module import RSIModule, CircuitState


class TestRSIModule(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file for testing
        self.test_config_file = "test_config.json"
        self.test_config = {
            "error_threshold": 0.1,
            "response_time_threshold": 0.5,
            "check_interval": 1,
            "loop_limit": 5,
        }
        with open(self.test_config_file, "w") as f:
            json.dump(self.test_config, f, indent=4)
        self.rsi = RSIModule(config_file=self.test_config_file)

    def tearDown(self):
        # Clean up the test config file after tests run.
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)

    def test_load_config(self):
        self.rsi.load_config()
        self.assertEqual(self.rsi.config["error_threshold"], 0.1)
        self.assertEqual(self.rsi.config["response_time_threshold"], 0.5)

    def test_improvement_tasks(self):
        # Provide metrics that require both tasks.
        metrics = {"error_rate": 0.2, "response_time": 0.6}
        tasks = self.rsi.improvement_tasks(metrics)
        self.assertIn("optimize_error_handling", tasks)
        self.assertIn("optimize_response_time", tasks)

    def test_execute_task_updates_config(self):
        # Run error handling optimization and test that threshold tightens.
        original_threshold = self.rsi.config["error_threshold"]
        self.rsi.execute_task("optimize_error_handling")
        self.assertLess(self.rsi.config["error_threshold"], original_threshold)

        # Run response time optimization and test that threshold tightens.
        original_rt = self.rsi.config["response_time_threshold"]
        self.rsi.execute_task("optimize_response_time")
        self.assertLess(self.rsi.config["response_time_threshold"], original_rt)

    def test_run_loop_safeguard(self):
        # Run the loop in a blocking way to test that it halts after loop_limit iterations.
        self.rsi.run_loop()
        self.assertGreaterEqual(self.rsi.loop_counter, self.test_config["loop_limit"])

    def test_circuit_breaker_recovery(self):
        """Test that system recovers after failures"""
        # Force failures to open circuit
        for _ in range(6):
            self.rsi.execute_task("failing_task")
        
        # Verify circuit is open
        self.assertEqual(
            self.rsi.resilience.circuit_breakers["sandbox"].state,
            CircuitState.OPEN
        )
        
        # Wait for recovery timeout
        time.sleep(1)  # Shortened for testing
        
        # Attempt recovery
        result = self.rsi.execute_task("healthy_task")
        
        # Verify circuit closed after successful execution
        self.assertEqual(
            self.rsi.resilience.circuit_breakers["sandbox"].state,
            CircuitState.CLOSED
        )

    def test_degraded_mode_operation(self):
        """Test system continues in degraded mode"""
        # Force system into degraded mode
        self.rsi.memory_manager = None
        
        # Execute directive
        directive = {"id": "test", "priority": "High", "code": "print('test')"}
        result = self.rsi.execute_directive()
        
        # Verify degraded execution
        self.assertTrue(self.rsi.degraded_mode)
        self.assertGreater(
            self.rsi.performance_metrics.get("degraded_executions", 0),
            0
        )


if __name__ == "__main__":
    unittest.main()
