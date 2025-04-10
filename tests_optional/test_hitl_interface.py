import unittest
from unittest.mock import Mock, patch
import json
from hitl_interface import HITLInterface

class TestHITLInterface(unittest.TestCase):
    def setUp(self):
        self.mock_task_manager = Mock()
        self.mock_code_analyzer = Mock()
        self.hitl = HITLInterface(
            task_manager=self.mock_task_manager,
            code_analyzer=self.mock_code_analyzer
        )

    def test_request_human_review(self):
        """Test human review request generation"""
        test_change = {
            "type": "code_modification",
            "file": "test.py",
            "changes": "test changes"
        }
        
        review_request = self.hitl.request_human_review(test_change)
        self.assertIn("request_id", review_request)
        self.assertIn("timestamp", review_request)
        self.assertIn("change_details", review_request)

    def test_process_human_feedback(self):
        """Test handling of human feedback"""
        feedback = {
            "request_id": "test_id",
            "approved": True,
            "comments": "Test feedback"
        }
        
        result = self.hitl.process_human_feedback(feedback)
        self.assertTrue(result["processed"])
        self.mock_task_manager.update_task.assert_called_once()

    def test_risk_assessment(self):
        """Test risk assessment of proposed changes"""
        test_changes = {
            "file": "critical_module.py",
            "modifications": ["function_change", "config_update"]
        }
        
        risk_level = self.hitl.assess_risk(test_changes)
        self.assertIn(risk_level, ["low", "medium", "high"])

    def test_feedback_validation(self):
        """Test validation of human feedback format"""
        invalid_feedback = {"invalid": "format"}
        
        with self.assertRaises(ValueError):
            self.hitl.process_human_feedback(invalid_feedback)

    def test_emergency_override(self):
        """Test emergency override functionality"""
        override_request = {
            "reason": "critical_bugfix",
            "priority": "high",
            "changes": "emergency fix"
        }
        
        result = self.hitl.emergency_override(override_request)
        self.assertTrue(result["override_applied"])
        self.mock_task_manager.prioritize_task.assert_called_once()

    def test_audit_trail(self):
        """Test audit trail generation"""
        test_action = {
            "type": "code_review",
            "user": "test_user",
            "action": "approve"
        }
        
        audit_entry = self.hitl.log_audit_trail(test_action)
        self.assertIn("timestamp", audit_entry)
        self.assertIn("action_details", audit_entry)

if __name__ == '__main__':
    unittest.main()