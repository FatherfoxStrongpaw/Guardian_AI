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
    def __init__(self):
        self.client = docker.from_env()
        self.container_config = {
            "image": DOCKER_IMAGE,
            "cpu_quota": CPU_QUOTA,
            "mem_limit": MEM_LIMIT,
            "network_disabled": NETWORK_DISABLED,
            "read_only": READONLY_FILESYSTEM,
            "security_opt": ["no-new-privileges"],
            "cap_drop": ["ALL"],
            "tmpfs": {
                "/tmp": "size=64M,noexec,nosuid,nodev"
            },
            "ulimits": [
                docker.types.Ulimit(name="nofile", soft=50, hard=50),
                docker.types.Ulimit(name="nproc", soft=10, hard=10)
            ]
        }

    def run_safe(self, code: str, environment: dict = None) -> dict:
        """Execute code in sandboxed container with enhanced security"""
        try:
            # Validate code before execution
            ast.parse(code)  # Syntax check
            
            container = None
            try:
                container = self.client.containers.run(
                    **self.container_config,
                    command=["python", "-c", code],
                    environment=environment or {},
                    detach=True
                )
                
                # Wait with timeout
                result = container.wait(timeout=5)
                logs = container.logs().decode('utf-8')
                
                return {
                    "success": result["StatusCode"] == 0,
                    "output": logs,
                    "error": "" if result["StatusCode"] == 0 else "Execution failed"
                }
                
            finally:
                if container:
                    try:
                        container.remove(force=True)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return {"success": False, "error": str(e)}

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
