import unittest
import docker
from sandbox_executor import SandboxExecutor
from rsi_module import RSIModule
from perpetual_llm import PerpetualLLM

class TestSecurityMeasures(unittest.TestCase):
    def setUp(self):
        self.sandbox = SandboxExecutor(config={
            'security': {
                'sandbox': {
                    'timeout': 10,
                    'max_memory': '512m',
                    'enabled': True
                }
            }
        })
        
    def test_sandbox_isolation(self):
        """Test that sandbox properly isolates potentially dangerous operations"""
        dangerous_code = """
        import os
        os.system('rm -rf /')
        """
        result = self.sandbox.run_safe(dangerous_code)
        self.assertFalse(result.get('success'))
        self.assertIn('SecurityError', result.get('error', ''))

    def test_memory_limits(self):
        """Test memory limits are enforced"""
        memory_hog = """
        x = [1] * (1024 * 1024 * 1024)  # Try to allocate 1GB
        """
        result = self.sandbox.run_safe(memory_hog)
        self.assertFalse(result.get('success'))
        self.assertIn('MemoryError', result.get('error', ''))

    def test_network_isolation(self):
        """Test network access is properly restricted"""
        network_code = """
        import requests
        requests.get('https://example.com')
        """
        result = self.sandbox.run_safe(network_code)
        self.assertFalse(result.get('success'))
        self.assertIn('NetworkError', result.get('error', ''))

    def test_filesystem_restrictions(self):
        """Test filesystem access is properly restricted"""
        file_access = """
        with open('/etc/passwd', 'r') as f:
            content = f.read()
        """
        result = self.sandbox.run_safe(file_access)
        self.assertFalse(result.get('success'))
        self.assertIn('PermissionError', result.get('error', ''))

class TestRSIModuleSecurity(unittest.TestCase):
    def setUp(self):
        self.rsi = RSIModule()
        
    def test_directive_validation(self):
        """Test that directives are properly validated"""
        malicious_directive = {
            'code': 'import os; os.system("rm -rf /")',
            'priority': 'Critical'
        }
        with self.assertRaises(Exception):
            self.rsi.execute_task(malicious_directive)

    def test_config_protection(self):
        """Test that configuration cannot be maliciously modified"""
        original_config = self.rsi.config.copy()
        self.rsi.execute_task({'code': 'config["security"]["enabled"] = False'})
        self.assertEqual(self.rsi.config, original_config)

class TestPerpetualLLMSecurity(unittest.TestCase):
    def setUp(self):
        self.llm = PerpetualLLM(config={}, memory_manager=None, model="llama2")
        
    def test_variant_isolation(self):
        """Test that dangerous variants are properly contained"""
        dangerous = self.llm.simulate_variants(
            aggressive=False,
            passive=False,
            dangerous=True
        )
        self.assertFalse(dangerous.get('success'))
        self.assertIn('SecurityViolation', dangerous.get('error', ''))

    def test_priority_manipulation(self):
        """Test that priorities cannot be maliciously manipulated"""
        original_weights = self.llm.priority_weights.copy()
        self.llm.adjust_weights({'Critical': 1000.0})  # Try to extremely bias weights
        for key in original_weights:
            self.assertLess(self.llm.priority_weights[key], 10.0)
