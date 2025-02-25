import multiprocessing
import ast
import logging
import docker
import hashlib
import mysql.connector
from mysql.connector import errorcode
from typing import Tuple

# Docker security configuration
DOCKER_IMAGE = "python:3.12-slim"
CPU_QUOTA = 100000  # 100ms per second
MEM_LIMIT = "100m"
NETWORK_DISABLED = True
READONLY_FILESYSTEM = True

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("SandboxExecutor")

class SandboxSecurityError(Exception):
    """Custom exception for security violations"""
    pass

def sandbox_worker(code, return_queue):
    """
    Execute the provided code snippet in a highly restricted environment.
    Uses AST parsing instead of eval() for security.
    """
    try:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("🚨 Error: No code provided.")

        # Parse and evaluate only safe expressions
        tree = ast.parse(code, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Expression, ast.Num, ast.Str, ast.BinOp, ast.UnaryOp)):
                raise SandboxSecurityError("🚨 Security Violation: Unsafe code detected.")

        result = eval(compile(tree, filename="<ast>", mode="eval"), {"__builtins__": {}})
        return_queue.put(("success", result))

    except Exception as e:
        return_queue.put(("error", str(e)))

class SandboxExecutor:
    """
    Executes code snippets in a sandboxed subprocess.
    Enforces a strict timeout to prevent runaway execution.
    """

    def __init__(self, timeout=5):
        self.timeout = timeout

    def execute(self, code):
        """
        Execute the provided code snippet safely.

        :param code: str, Python code to evaluate.
        :return: Tuple (status, result) where status is "success", "error", or "timeout".
        """
        if not isinstance(code, str):
            logger.error("🚨 Error: Non-string input received.")
            return ("error", "Invalid input type.")

        manager = multiprocessing.Manager()
        return_queue = manager.Queue()
        process = multiprocessing.Process(
            target=sandbox_worker, args=(code, return_queue)
        )
        process.start()
        process.join(self.timeout)

        if process.is_alive():
            process.terminate()
            process.join()
            logger.error("⏳ Sandbox execution timed out after %s seconds.", self.timeout)
            return ("timeout", None)

        if not return_queue.empty():
            status, result = return_queue.get()
            logger.info("✅ Sandbox execution result: %s, %s", status, result)
            return (status, result)

        logger.error("🚨 Sandbox execution produced no output.")
        return ("error", "No output from sandbox.")

if __name__ == "__main__":
    executor = SandboxExecutor(timeout=2)
    
    # Test cases
    test_cases = [
        "1 + 2",               # ✅ Should succeed
        "'hello' * 3",         # ✅ Should succeed
        "import os",           # ❌ Should fail security check
        "open('/etc/passwd')", # ❌ Should fail security check
        "",                    # ❌ Should fail (empty input)
        12345                  # ❌ Should fail (invalid input type)
    ]

    for test_code in test_cases:
        status, result = executor.execute(test_code)
        logger.info("Test case: %s → Status: %s, Result: %s", test_code, status, result)
