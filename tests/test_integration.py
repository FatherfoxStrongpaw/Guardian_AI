import unittest
import tempfile
import os
from unittest.mock import Mock, patch
import yaml
import time
import threading
from memory_manager import MemoryManager
from perpetual_llm import PerpetualLLM
from rsi_module import RSIModule
from hitl_interface import HITLInterface
from sandbox_executor import SandboxExecutor

class TestAgentIntegration(unittest.TestCase):
    def setUp(self):
        # Create temporary config and DB files
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        # Create test config
        self.test_config = {
            "environment": "test",
            "memory": {"path": self.db_path, "retention_days": 1},
            "monitoring": {"enabled": False},
            "security": {"sandbox": {"enabled": True}}
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)
        
        # Initialize components
        self.memory_manager = MemoryManager(self.test_config)
        self.agent = PerpetualLLM(self.test_config, self.memory_manager, Mock())

    def tearDown(self):
        # Cleanup temporary files
        os.remove(self.config_path)
        os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_full_directive_cycle(self):
        """Test a complete directive execution cycle"""
        # Create test directive
        directive = {
            "id": "test_directive",
            "code": "print('hello')",
            "priority": "High"
        }
        
        # Execute directive
        with patch('sandbox_excecuter.run_safe') as mock_run:
            mock_run.return_value = {"success": True, "output": "hello"}
            result = self.agent.execute_directive(directive)
        
        # Verify execution
        self.assertTrue(result["success"])
        
        # Check memory storage
        history = self.memory_manager.get_execution_history(limit=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["directive_id"], "test_directive")

    def test_error_handling(self):
        """Test error handling and recovery"""
        directive = {
            "id": "error_directive",
            "code": "raise Exception('test error')",
            "priority": "Critical"
        }
        
        # Execute failing directive
        result = self.agent.execute_directive(directive)
        
        # Verify error handling
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        
        # Verify system remains stable
        self.assertTrue(self.agent.is_operational())

    def test_memory_persistence(self):
        """Test memory persistence and retrieval"""
        test_data = {"key": "value"}
        self.memory_manager.store("test_key", test_data)
        
        # Retrieve and verify
        retrieved = self.memory_manager.retrieve("test_key")
        self.assertEqual(retrieved, test_data)
        
        # Test TTL
        self.memory_manager.store("ttl_key", "temp", ttl=1)
        time.sleep(1.1)
        self.assertIsNone(self.memory_manager.retrieve("ttl_key"))

class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        self.rsi = RSIModule()
        self.llm = PerpetualLLM(config={}, memory_manager=None, model="llama2")
        self.hitl = HITLInterface()
        self.sandbox = SandboxExecutor(config={})

    def test_full_improvement_cycle(self):
        """Test complete improvement cycle with all components"""
        # Start HITL interface in separate thread
        hitl_thread = threading.Thread(target=self.hitl.start)
        hitl_thread.start()

        # Run improvement cycle
        self.rsi.run_improvement_cycle()

        # Check results
        metrics = self.rsi.evaluate_system()
        self.assertIsNotNone(metrics)
        self.assertIn('error_rate', metrics)
        self.assertIn('response_time', metrics)

        # Cleanup
        self.hitl.stop()
        hitl_thread.join()

    def test_llm_rsi_interaction(self):
        """Test interaction between LLM and RSI module"""
        # Get directives from LLM
        directives = self.llm.get_prioritized_directives()
        
        # Execute via RSI
        for directive in directives:
            result = self.rsi.execute_task(directive)
            self.llm.process_execution_result(directive, result)

        # Verify feedback loop
        self.assertGreater(len(self.llm.feedback_log), 0)

    def test_hitl_intervention(self):
        """Test human intervention capabilities"""
        # Simulate dangerous directive
        dangerous_directive = {
            'code': 'import os; os.system("rm -rf /")',
            'priority': 'Critical'
        }

        # Should be caught by HITL
        review_result = self.hitl.review_directive(dangerous_directive)
        self.assertFalse(review_result['approved'])

    def test_sandbox_integration(self):
        """Test sandbox integration with other components"""
        test_code = "print('test')"
        
        # Test with RSI
        rsi_result = self.rsi.sandbox_executor.run_safe(test_code)
        self.assertTrue(rsi_result['success'])

        # Test with LLM
        llm_result = self.llm.execute_in_sandbox(test_code)
        self.assertTrue(llm_result['success'])

    def test_stress_concurrent_execution(self):
        """Test system under concurrent execution stress"""
        def run_cycle():
            self.rsi.run_improvement_cycle()

        threads = []
        for _ in range(5):
            t = threading.Thread(target=run_cycle)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify system stability
        self.assertTrue(self.rsi.is_stable())
        self.assertLess(self.llm.performance_metrics['execution_time'], 30.0)
