import unittest
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch
from memory_manager import MemoryManager

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.config = {
            "memory": {
                "path": self.db_path,
                "type": "sqlite",
                "retention_days": 7
            }
        }
        self.memory_manager = MemoryManager(self.config)

    def tearDown(self):
        self.memory_manager.cleanup()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_record_management(self):
        """Test basic record operations"""
        # Add record
        test_record = {
            "type": "execution",
            "data": {"code": "test", "result": "success"}
        }
        record_id = self.memory_manager.add_record(test_record)
        self.assertIsNotNone(record_id)

        # Retrieve record
        retrieved = self.memory_manager.get_record(record_id)
        self.assertEqual(retrieved["data"]["code"], "test")

        # Update record
        updated_data = {"code": "test", "result": "updated"}
        self.memory_manager.update_record(record_id, updated_data)
        updated = self.memory_manager.get_record(record_id)
        self.assertEqual(updated["data"]["result"], "updated")

    def test_query_operations(self):
        """Test query functionality"""
        # Add test records
        records = [
            {"type": "execution", "data": {"code": "test1", "result": "success"}},
            {"type": "execution", "data": {"code": "test2", "result": "failure"}},
            {"type": "snapshot", "data": {"state": "stable"}}
        ]
        for record in records:
            self.memory_manager.add_record(record)

        # Query by type
        executions = self.memory_manager.query_records({"type": "execution"})
        self.assertEqual(len(executions), 2)

        # Query by content
        failures = self.memory_manager.query_records({"data.result": "failure"})
        self.assertEqual(len(failures), 1)

    def test_retention_policy(self):
        """Test data retention policy"""
        with patch('time.time') as mock_time:
            # Add old record
            mock_time.return_value = 1000000  # Past timestamp
            self.memory_manager.add_record({"type": "old", "data": {}})

            # Add new record
            mock_time.return_value = 9999999999  # Future timestamp
            self.memory_manager.add_record({"type": "new", "data": {}})

            # Clean up old records
            cleaned = self.memory_manager.cleanup_old_records()
            self.assertTrue(cleaned > 0)

            # Verify old record is gone
            records = self.memory_manager.query_records({"type": "old"})
            self.assertEqual(len(records), 0)

    def test_performance_metrics(self):
        """Test performance tracking"""
        # Record some operations
        for _ in range(10):
            self.memory_manager.add_record({"type": "test", "data": {}})

        metrics = self.memory_manager.get_performance_metrics()
        self.assertIn("total_records", metrics)
        self.assertIn("avg_query_time", metrics)

    def test_backup_restore(self):
        """Test backup and restore functionality"""
        # Add some test data
        test_data = {"type": "test", "data": {"important": "data"}}
        self.memory_manager.add_record(test_data)

        # Create backup
        backup_path = os.path.join(self.temp_dir, "backup.db")
        self.memory_manager.create_backup(backup_path)
        self.assertTrue(os.path.exists(backup_path))

        # Restore from backup
        new_db_path = os.path.join(self.temp_dir, "restored.db")
        self.memory_manager.restore_from_backup(backup_path, new_db_path)

        # Verify restored data
        restored_manager = MemoryManager({"memory": {"path": new_db_path}})
        restored_records = restored_manager.query_records({"type": "test"})
        self.assertEqual(len(restored_records), 1)
        self.assertEqual(restored_records[0]["data"]["important"], "data")

    def test_error_handling(self):
        """Test error handling in database operations"""
        # Test invalid record
        with self.assertRaises(ValueError):
            self.memory_manager.add_record(None)

        # Test invalid query
        with self.assertRaises(ValueError):
            self.memory_manager.query_records(None)

        # Test database connection error
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Test error")
            with self.assertRaises(Exception):
                MemoryManager(self.config)

    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        # Test that circuit breaker is initialized
        self.assertIsNotNone(self.memory_manager.db_circuit_breaker)

        # Test that circuit breaker is used for store operations
        with patch.object(self.memory_manager.db_circuit_breaker, 'execute') as mock_execute:
            mock_execute.return_value = True
            self.memory_manager.store("test_key", "test_value")
            mock_execute.assert_called_once()

        # Test that circuit breaker is used for retrieve operations
        with patch.object(self.memory_manager.db_circuit_breaker, 'execute') as mock_execute:
            mock_execute.return_value = '{"value": "test_value"}'
            self.memory_manager.retrieve("test_key")
            mock_execute.assert_called_once()

        # Test fallback behavior
        with patch.object(self.memory_manager, '_db_operation_fallback') as mock_fallback:
            mock_fallback.return_value = None
            # Force circuit breaker to use fallback
            self.memory_manager.db_circuit_breaker.failure_count = 999
            self.memory_manager.db_circuit_breaker.state = 2  # OPEN state
            result = self.memory_manager.retrieve("test_key")
            self.assertIsNone(result)
            mock_fallback.assert_called_once()

if __name__ == '__main__':
    unittest.main()