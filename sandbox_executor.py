import logging
import docker
import ast
import tempfile
import os
import multiprocessing
import hashlib
from typing import Tuple, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    DEFAULT_CONFIG = {
        'security': {
            'sandbox': {
                'timeout': 10,
                'max_memory': '512m',
                'enabled': True,
                'cpu_quota': 100000,  # 100ms per second
                'network_disabled': True,
                'readonly_filesystem': True
            }
        }
    }

    def __init__(self, config):
        self.config = config or self.DEFAULT_CONFIG

        # Get sandbox config with defaults
        sandbox_config = self.config.get('security', {}).get('sandbox', {})
        self.timeout = sandbox_config.get('timeout', 10)
        self.max_memory = sandbox_config.get('max_memory', '512m')
        self.cpu_quota = sandbox_config.get('cpu_quota', 100000)
        self.network_disabled = sandbox_config.get('network_disabled', True)
        self.readonly_filesystem = sandbox_config.get('readonly_filesystem', True)
        self.docker_client = docker.from_env()

        # Enhanced security configuration
        self.container_config = {
            "image": "python:3.12-slim",
            "cpu_quota": self.cpu_quota,
            "mem_limit": self.max_memory,
            "network_disabled": self.network_disabled,
            "read_only": self.readonly_filesystem,
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

        logger.info(f"Initialized SandboxExecutor with timeout={self.timeout}, max_memory={self.max_memory}")

    def validate_code(self, code: str) -> bool:
        """Validate code for security issues"""
        try:
            # Basic syntax check
            ast.parse(code)

            # Check for dangerous imports
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in ['os', 'subprocess', 'sys', 'shutil']:
                            logger.warning(f"Security violation: Attempted to import restricted module {name.name}")
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ['os', 'subprocess', 'sys', 'shutil']:
                        logger.warning(f"Security violation: Attempted to import from restricted module {node.module}")
                        return False

            return True
        except SyntaxError as e:
            logger.warning(f"Code validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during code validation: {e}")
            return False

    def run_safe(self, code: str, environment: dict = None, timeout: int = None) -> dict:
        """
        Safely execute code in a sandboxed Docker container with enhanced security
        """
        if timeout is None:
            timeout = self.timeout

        try:
            # Validate code before execution
            if not self.validate_code(code):
                return {
                    "success": False,
                    "error": "SecurityError: Code validation failed"
                }

            # Try simple expression evaluation first for better security
            if len(code.strip().split('\n')) == 1 and not any(keyword in code for keyword in ['import', 'exec', 'eval']):
                try:
                    manager = multiprocessing.Manager()
                    return_queue = manager.Queue()
                    process = multiprocessing.Process(target=sandbox_worker, args=(code, return_queue))
                    process.start()
                    process.join(timeout)

                    if process.is_alive():
                        process.terminate()
                        process.join()
                        return {"success": False, "error": "Execution timed out"}

                    if not return_queue.empty():
                        status, result = return_queue.get()
                        if status == "success":
                            return {"success": True, "output": str(result)}
                        else:
                            # If simple evaluation fails, continue to Docker sandbox
                            logger.info(f"Simple evaluation failed, using Docker sandbox: {result}")
                except Exception as simple_eval_error:
                    logger.info(f"Simple evaluation not applicable, using Docker sandbox: {simple_eval_error}")

            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_path = f.name

            try:
                # Prepare environment variables
                env_vars = environment or {}

                # Create a copy of container_config to avoid modifying the original
                container_config = self.container_config.copy()
                container_config["command"] = ["python", "-c", code]
                container_config["environment"] = env_vars
                container_config["detach"] = True

                # Run in container with enhanced security limits
                container = self.docker_client.containers.run(**container_config)

                try:
                    result = container.wait(timeout=timeout)
                    output = container.logs().decode('utf-8')

                    return {
                        "success": result["StatusCode"] == 0,
                        "output": output,
                        "error": "" if result["StatusCode"] == 0 else "Execution failed"
                    }
                finally:
                    # Always clean up the container
                    try:
                        container.remove(force=True)
                    except Exception as container_error:
                        logger.warning(f"Error removing container: {container_error}")

            finally:
                # Cleanup temporary file
                if os.path.exists(code_path):
                    os.unlink(code_path)

        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute(self, command: str, environment: dict = None) -> dict:
        """
        Execute a command in the sandbox
        This is an async wrapper around run_safe for compatibility with the async API
        """
        # For shell commands, wrap in a Python script that uses subprocess
        code = f"""
        import subprocess
        import sys

        try:
            result = subprocess.run(
                {repr(command)},
                shell=True,
                capture_output=True,
                text=True,
                timeout={self.timeout}
            )
            print(result.stdout)
            if result.stderr:
                print("ERROR:", result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Execution error: {{e}}", file=sys.stderr)
            sys.exit(1)
        """

        return self.run_safe(code, environment)
