import logging
import docker
import ast
from pathlib import Path
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SandboxExecutor:
    DEFAULT_CONFIG = {
        'security': {
            'sandbox': {
                'timeout': 10,
                'max_memory': '512m',
                'enabled': True
            }
        }
    }

    def __init__(self, config):
        self.config = config or self.DEFAULT_CONFIG
        
        # Get sandbox config with defaults
        sandbox_config = self.config.get('security', {}).get('sandbox', {})
        self.timeout = sandbox_config.get('timeout', 10)
        self.max_memory = sandbox_config.get('max_memory', '512m')
        self.docker_client = docker.from_env()
        
        logger.info(f"Initialized SandboxExecutor with timeout={self.timeout}, max_memory={self.max_memory}")
        
    def run_safe(self, code: str, environment: dict = None, timeout: int = None) -> dict:
        """
        Safely execute code in a sandboxed Docker container
        """
        if timeout is None:
            timeout = self.timeout

        try:
            # Validate code before execution
            ast.parse(code)
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_path = f.name

            try:
                # Run in container with limits
                container = self.docker_client.containers.run(
                    "python:3.12-slim",
                    command=f"python {code_path}",
                    mem_limit=self.max_memory,
                    network_mode="none",
                    remove=True,
                    detach=True
                )
                
                result = container.wait(timeout=timeout)
                output = container.logs().decode('utf-8')
                
                return {
                    "success": result["StatusCode"] == 0,
                    "output": output
                }
                
            finally:
                # Cleanup
                os.unlink(code_path)
                
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
