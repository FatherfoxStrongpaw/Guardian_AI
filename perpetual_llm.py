import logging
import time
import os
import io
import contextlib
import multiprocessing
from typing import Dict, Union, List, Tuple, Any, Optional
from threading import Event, Lock
from datetime import datetime
import hashlib
import asyncio
import yaml
from dataclasses import dataclass
from resilience.circuit_breaker import CircuitBreaker

from rsi_module import RSIModule
from ollama_agent import OllamaAgent
from memory_manager import MemoryManager
from sandbox_executor import SandboxExecutor
from hitl_interface import HITLInterface

logger = logging.getLogger(__name__)

# Define a set of safe built-in functions for code interpretation
SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "abs": abs,
    "sum": sum,
    "min": min,
    "max": max,
    "sorted": sorted,
    "enumerate": enumerate,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "round": round
}

def interpreter_worker(code, return_queue):
    """
    Execute the provided multi-line code snippet in a restricted environment.
    Captures standard output and error messages.
    """
    try:
        # Create StringIO buffers to capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Set up a restricted global namespace with safe built-ins
        restricted_globals = {"__builtins__": SAFE_BUILTINS}
        local_vars = {}

        # Redirect stdout and stderr
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, restricted_globals, local_vars)

        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()
        return_queue.put(("success", output, errors, local_vars))
    except Exception as e:
        return_queue.put(("error", "", str(e), {}))

class CodeInterpreter:
    """
    A Code Interpreter that safely executes Python code snippets in a sandboxed subprocess.
    Captures both output and error messages while enforcing a timeout.
    """

    def __init__(self, timeout=5):
        self.timeout = timeout
        logger.info(f"Initialized CodeInterpreter with timeout={timeout}s")

    def execute(self, code: str) -> Tuple[str, str, str, Dict]:
        """
        Execute the given code snippet.

        Args:
            code: Python code to execute

        Returns:
            Tuple (status, output, error_message, local_vars) where status can be "success", "error", or "timeout".
        """
        manager = multiprocessing.Manager()
        return_queue = manager.Queue()
        process = multiprocessing.Process(target=interpreter_worker, args=(code, return_queue))
        process.start()
        process.join(self.timeout)

        if process.is_alive():
            process.terminate()
            process.join()
            logger.error(f"Code interpretation timed out after {self.timeout} seconds")
            return ("timeout", "", "Execution timed out", {})

        if not return_queue.empty():
            status, output, error_message, local_vars = return_queue.get()
            logger.info(f"Code interpretation result: {status}")
            if output:
                logger.debug(f"Output:\n{output}")
            if error_message:
                logger.debug(f"Error:\n{error_message}")
            return (status, output, error_message, local_vars)

        logger.error("Code interpretation produced no output")
        return ("error", "", "No output from interpreter", {})

@dataclass
class SecurityContext:
    """Security context for command execution"""
    allowed_modules: List[str]
    max_tokens: int
    timeout: int
    sandbox_enabled: bool = True
    trust_level: int = 100
    requires_hitl: bool = False
    memory_limit: str = "512m"

class CommandValidator:
    """Validates and categorizes commands"""
    def __init__(self, config: dict):
        self.config = config
        self.blocked_patterns = [
            "rm -rf",
            "sudo",
            "chmod",
            "chown",
            "eval(",
            "exec(",
        ]

    def get_security_context(self, command: str) -> SecurityContext:
        """Determine security context for a command"""
        trust_level = 100  # Start with full trust

        # Reduce trust based on patterns
        for pattern in self.blocked_patterns:
            if pattern in command:
                trust_level = 0
                break

        # Analyze command complexity
        if len(command.split()) > 10:
            trust_level -= 20

        requires_hitl = trust_level < 80

        # Get sandbox config with defaults
        sandbox_config = self.config.get("security", {}).get("sandbox", {})
        allowed_modules = sandbox_config.get("allowed_modules", ["os", "sys", "time", "json"])
        timeout = sandbox_config.get("timeout", 10)
        max_tokens = sandbox_config.get("max_tokens", 2048)
        memory_limit = sandbox_config.get("max_memory", "512m")
        sandbox_enabled = sandbox_config.get("enabled", True)

        return SecurityContext(
            trust_level=trust_level,
            requires_hitl=requires_hitl,
            allowed_modules=allowed_modules,
            timeout=timeout,
            max_tokens=max_tokens,
            memory_limit=memory_limit,
            sandbox_enabled=sandbox_enabled
        )

class SystemMonitor:
    """Monitors system health and performance"""
    def __init__(self):
        self.start_time = datetime.now()
        self.command_history = []
        self.error_count = 0
        self.last_health_check = None

    def health_check(self) -> Dict[str, Union[str, int, float]]:
        """Perform system health check"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        error_rate = self.error_count / len(self.command_history) if self.command_history else 0

        self.last_health_check = datetime.now()

        return {
            "status": "healthy" if error_rate < 0.1 else "degraded",
            "uptime": uptime,
            "error_rate": error_rate,
            "commands_processed": len(self.command_history),
            "last_check": self.last_health_check.isoformat()
        }

class PerpetualLLM:
    def __init__(self, config_path: str, memory_manager: MemoryManager, model: str = "llama2"):
        """Initialize the Perpetual LLM agent"""
        self.config_path = config_path

        # Verify config file exists
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}. Creating with defaults.")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(self.get_default_config(), f)

        # Load config
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Initialize security and monitoring
        self.validator = CommandValidator(self.config)
        self.monitor = SystemMonitor()

        # Initialize circuit breakers for critical operations
        self.file_io_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            fallback=self._file_io_fallback
        )

        # Initialize components with enhanced security
        self.memory_manager = memory_manager
        self.sandbox = SandboxExecutor(self.config)
        self.hitl = HITLInterface(self.config)
        self.code_interpreter = CodeInterpreter(timeout=self.config.get("security", {}).get("sandbox", {}).get("timeout", 10))

        # Initialize RSI module with security context
        self.rsi_module = RSIModule(
            config_file=config_path,
            memory_manager_instance=memory_manager,
            sandbox_executor=self.sandbox
        )

        # Initialize Ollama agent with circuit breaker
        self.ollama = OllamaAgent(
            model=self.config.get("llm", {}).get("model", model),
            base_url=self.config.get("llm", {}).get("api", {}).get("base_url", "http://localhost:11434"),
            failure_threshold=3,
            recovery_timeout=60
        )

        # Control flags and locks
        self.running = False
        self.shutdown_event = Event()
        self.command_lock = Lock()

        # Performance metrics
        self.metrics = {
            "directive_success_rate": 0.0,
            "response_time": 0.0,
            "error_rate": 0.0
        }

        # Priority layers and weights for directive execution
        self.priority_layers = {
            "Critical": [],
            "High": [],
            "Moderate": [],
            "Peripheral": []
        }

        self.priority_weights = {
            "Critical": 0.5,
            "High": 0.3,
            "Moderate": 0.15,
            "Peripheral": 0.05
        }

        # Variant performance tracking
        self.variant_performance = {
            "aggressive": 0,
            "passive": 0,
            "dangerous": 0
        }

    def _file_io_fallback(self, operation="read", file_path="unknown"):
        """Fallback for file I/O operations when circuit breaker is open"""
        logger.warning(f"Circuit breaker is open for file I/O operations on {file_path}, using fallback")

        if operation == "read":
            return None
        elif operation == "write":
            return False
        elif operation == "verify":
            return False
        else:
            return None

    async def handle_degraded_state(self, health_status: dict):
        """Handle degraded system state"""
        logger.warning("System in degraded state - initiating recovery")

        # Notify HITL
        await self.hitl.alert_degraded_state(health_status)

        # Attempt self-healing
        try:
            result = await self.rsi_module.self_heal()
            logger.info(f"Self-healing result: {result}")
        except Exception as e:
            logger.error(f"Self-healing failed: {e}")

    def _read_file_with_circuit_breaker(self, file_path):
        """Read a file with circuit breaker protection"""
        try:
            return self.file_io_circuit_breaker.execute(
                lambda: open(file_path, 'rb').read(),
                operation="read",
                file_path=file_path
            )
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    def verify_file_integrity(self) -> bool:
        """Verify integrity of critical files with circuit breaker protection"""
        critical_files = [
            "perpetual_llm.py",
            "rsi_module.py",
            "sandbox_executor.py",
            "hitl_interface.py",
            "ollama_agent.py"
        ]

        all_files_ok = True
        results = {}

        for file in critical_files:
            try:
                if not os.path.exists(file):
                    logger.error(f"Critical file not found: {file}")
                    results[file] = {"status": "missing"}
                    all_files_ok = False
                    continue

                # Use circuit breaker to read file
                content = self._read_file_with_circuit_breaker(file)
                if content is None:
                    logger.error(f"Failed to read {file} (circuit breaker may be open)")
                    results[file] = {"status": "read_error"}
                    all_files_ok = False
                    continue

                current_hash = hashlib.sha256(content).hexdigest()
                results[file] = {"current_hash": current_hash}

                # Check if memory_manager has the required methods
                if not hasattr(self.memory_manager, 'get_hash') or not hasattr(self.memory_manager, 'store_hash'):
                    logger.warning(f"Memory manager missing hash methods, skipping hash verification")
                    results[file]["status"] = "not_verified"
                    continue

                # Compare with stored hash
                stored_hash = self.memory_manager.get_hash(file)
                results[file]["stored_hash"] = stored_hash

                if stored_hash and stored_hash != current_hash:
                    logger.error(f"Integrity check failed for {file}")
                    results[file]["status"] = "modified"
                    all_files_ok = False
                else:
                    results[file]["status"] = "ok"
                    # Store new hash if none exists
                    if not stored_hash:
                        try:
                            self.memory_manager.store_hash(file, current_hash)
                            logger.info(f"Stored new hash for {file}")
                        except Exception as store_err:
                            logger.warning(f"Failed to store hash for {file}: {store_err}")

            except Exception as e:
                logger.error(f"Failed to verify {file}: {e}")
                results[file] = {"status": "error", "error": str(e)}
                all_files_ok = False

        # Log summary
        logger.info(f"File integrity check completed: {all_files_ok}")
        return all_files_ok

    async def process_input(self, user_input: str) -> Dict:
        """Process user input and execute appropriate action"""
        try:
            # Track command for monitoring
            self.monitor.command_history.append(user_input)
            start_time = time.time()

            result = None
            try:
                if user_input.startswith("!"):
                    result = await self.handle_command(user_input[1:])
                else:
                    response = await self.ollama.generate_response(user_input)
                    result = {"status": "success", "response": response}
            except Exception as cmd_error:
                self.monitor.error_count += 1
                logger.error(f"Command execution error: {cmd_error}")
                result = {"status": "error", "error": str(cmd_error)}

            # Update metrics
            execution_time = time.time() - start_time
            self.metrics["response_time"] = (self.metrics["response_time"] + execution_time) / 2  # Running average

            if result["status"] == "success":
                success_rate = self.metrics["directive_success_rate"]
                self.metrics["directive_success_rate"] = 0.9 * success_rate + 0.1 * 1.0  # Weighted update
            else:
                success_rate = self.metrics["directive_success_rate"]
                self.metrics["directive_success_rate"] = 0.9 * success_rate + 0.1 * 0.0  # Weighted update

            # Check system health periodically
            if len(self.monitor.command_history) % 10 == 0:  # Every 10 commands
                health = self.monitor.health_check()
                if health["status"] == "degraded":
                    asyncio.create_task(self.handle_degraded_state(health))

            return result

        except Exception as e:
            logger.error(f"Critical error processing input: {e}")
            return {"status": "error", "error": f"Critical error: {str(e)}"}

    async def handle_command(self, command: str) -> Dict:
        """Handle system commands"""
        parts = command.split()
        cmd = parts[0].lower()

        # Define command handlers as instance methods
        commands = {
            "rsi": self.handle_rsi_command,
            "system": self.handle_system_command,
            "analyze": self.handle_analysis_command,
            "status": self.get_system_status,
            "help": self.show_help,
            "consider_self": self.run_self_diagnostic,  # Add new command
            "interpret": self.handle_code_interpretation  # Add code interpreter command
        }

        handler = commands.get(cmd)
        if handler:
            return await handler(parts[1:] if len(parts) > 1 else [])

        return {"status": "error", "error": "Unknown command"}

    async def handle_rsi_command(self, args: List[str]) -> Dict:
        """Handle RSI-related commands"""
        if not args:
            return {"status": "error", "error": "RSI command requires arguments"}

        action = args[0]
        try:
            if action == "status":
                metrics = self.rsi_module.evaluate_system()
                return {"status": "success", "response": metrics}
            elif action == "optimize":
                result = await self.rsi_module.self_improve()
                return {"status": "success", "response": result}
            else:
                return {"status": "error", "error": "Unknown RSI action"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def handle_system_command(self, args: List[str]) -> Dict:
        """Handle system-level commands"""
        if not args:
            return {"status": "error", "error": "System command requires arguments"}

        command = " ".join(args)
        security_context = self.validator.get_security_context(command)

        if not security_context.sandbox_enabled:
            return {"status": "error", "error": "Command not allowed in current security context"}

        try:
            result = await self.sandbox.execute(command)
            return {"status": "success", "response": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def handle_analysis_command(self, args: List[str]) -> Dict:
        """Handle analysis commands"""
        if not args:
            return {"status": "error", "error": "Analysis command requires arguments"}

        try:
            action = args[0].lower()
            if action == "health":
                metrics = self.monitor.health_check()
                return {"status": "success", "response": metrics}
            elif action == "dependencies":
                # This would be implemented to analyze code dependencies
                return {"status": "success", "response": "Dependency analysis not implemented yet"}
            else:
                return {"status": "error", "error": f"Unknown analysis action: {action}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_system_status(self, args: List[str] = None) -> Dict:
        """Get current system status"""
        try:
            health = self.monitor.health_check()
            metrics = self.metrics.copy()
            metrics.update(health)

            # If args are provided, filter the metrics
            if args and len(args) > 0:
                filtered_metrics = {}
                for key in args:
                    if key in metrics:
                        filtered_metrics[key] = metrics[key]
                return {"status": "success", "response": filtered_metrics}

            return {"status": "success", "response": metrics}
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"status": "error", "error": str(e)}

    async def handle_code_interpretation(self, args: List[str]) -> Dict:
        """Handle code interpretation requests

        This method provides a safer alternative to the sandbox for simple code execution.
        It uses the CodeInterpreter which runs code in a subprocess with restricted builtins.

        Usage: !interpret <code>
        Example: !interpret print('Hello, world!')
        """
        if not args:
            return {"status": "error", "error": "No code provided for interpretation"}

        # Join all arguments to get the full code
        code = " ".join(args)

        try:
            # Check security context
            security_context = self.validator.get_security_context(code)
            if security_context.trust_level < 50:
                return {"status": "error", "error": "Code contains potentially unsafe patterns"}

            # Execute the code using the interpreter
            status, output, error, local_vars = self.code_interpreter.execute(code)

            # Format the response
            if status == "success":
                response = {
                    "output": output.strip() if output else "(No output)",
                    "variables": {k: str(v) for k, v in local_vars.items() if not k.startswith("_")}
                }
                return {"status": "success", "response": response}
            else:
                return {"status": "error", "error": error or "Unknown error during code interpretation"}
        except Exception as e:
            logger.error(f"Error during code interpretation: {e}")
            return {"status": "error", "error": str(e)}

    def run(self):
        """Main execution loop"""
        self.running = True
        print("\n🤖 Guardian AI initialized. Type !help for commands.")
        print("Use '!' prefix for local shell commands")

        # Start the RSI module
        self.rsi_module.start()

        # Start the HITL interface
        self.hitl.start()

        while self.running:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    confirm = input("⚠️ Are you sure you want to exit? (y/n): ").strip().lower()
                    if confirm == "y":
                        self.running = False
                        print("Shutting down Guardian AI...")
                        break
                    else:
                        continue

                # Handle local commands (!) - from perpetual_agent_old.py
                if user_input.startswith("!"):
                    local_command = user_input[1:].strip()
                    tokens = local_command.split()

                    if not tokens:
                        print("⚠️ No command provided after '!'. Please enter a valid local command.")
                        continue

                    # Special handling for analysis commands
                    if tokens[0].lower() in ["analyze", "check", "summarize"]:
                        try:
                            import subprocess
                            output = subprocess.check_output(local_command, shell=True, universal_newlines=True)
                        except subprocess.CalledProcessError as e:
                            output = f"⚠️ Error executing local command: {e}"

                        # Use Ollama to analyze the output
                        prompt = f"Please analyze the following output and provide insights:\n{output}"
                        response = asyncio.run(self.ollama.generate_response(prompt))

                        print("\n🔍 Local Command Output:")
                        print(output)
                        print("\n🤖 Analysis:")
                        print(response)

                    # General command execution
                    else:
                        try:
                            import subprocess
                            output = subprocess.check_output(local_command, shell=True, universal_newlines=True)
                            print("\n🖥️ Local Command Output:")
                            print(output)
                        except subprocess.CalledProcessError as e:
                            print(f"\n⚠️ Error executing local command: {e}")
                        except FileNotFoundError:
                            print(f"\n⚠️ Unknown command: '{local_command}' is not recognized.")
                        except Exception as e:
                            print(f"\n⚠️ Unexpected error executing '{local_command}': {e}")

                    continue

                # Default: Process through the agent
                result = asyncio.run(self.process_input(user_input))

                if result["status"] == "success":
                    # Check if the response is a dictionary or string
                    if isinstance(result["response"], dict):
                        print("\n🤖 Response:")
                        for key, value in result["response"].items():
                            print(f"  {key}: {value}")
                    else:
                        print("\n🤖 Response:", result["response"])
                else:
                    print("\n⚠️ Error:", result["error"])

            except KeyboardInterrupt:
                print("\nReceived keyboard interrupt. Shutting down...")
                self.running = False
            except EOFError:
                print("\nInput stream closed. Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"\n⚠️ Unexpected error: {e}")

    async def show_help(self, args: List[str] = None) -> Dict:
        """Show available commands and usage"""
        # If args are provided, show specific help
        if args and len(args) > 0:
            command = args[0].lower()
            if command == "rsi":
                help_text = """
RSI Commands:
------------
!rsi status   : Show current RSI system metrics
!rsi optimize : Run self-improvement cycle
"""
            elif command == "analyze":
                help_text = """
Analyze Commands:
---------------
!analyze health       : Check system health metrics
!analyze dependencies : Analyze code dependencies
"""
            elif command == "system":
                help_text = """
System Commands:
--------------
!system <command> : Execute a system command in the sandbox
                   Note: Commands are restricted for security
"""
            elif command == "interpret":
                help_text = """
Code Interpreter:
---------------
!interpret <code> : Execute Python code in a safe interpreter
                   Examples:
                   !interpret print('Hello, world!')
                   !interpret x = 5; y = 10; print(x + y)

                   Note: The interpreter has limited built-ins for security
                   Available functions: print, range, len, abs, sum, min, max,
                   sorted, enumerate, list, dict, set, tuple, str, int, float,
                   bool, round
"""
            else:
                help_text = f"No specific help available for '{command}'"
        else:
            # General help
            help_text = """
Available Commands:
-----------------
!rsi <command>      : Execute RSI-related operations
!analyze <input>    : Analyze system output or behavior
!system <command>   : Execute system commands (sandboxed)
!interpret <code>   : Execute Python code in a safe interpreter
!help [command]     : Show this help message or specific command help
!status [metrics]   : Show system status or specific metrics
!consider_self      : Run system self-diagnostics
"""

        # Return the help text in the response instead of printing it
        return {"status": "success", "response": help_text}

    async def run_self_diagnostic(self, args: List[str] = None) -> Dict:
        """Run system self-diagnostics"""
        try:
            # Get critical files from manifest
            critical_files = [
                "perpetual_llm.py",
                "rsi_module.py",
                "sandbox_executor.py",
                "hitl_interface.py",
                "ollama_agent.py",
                "self_diagnostic.py"
            ]

            # If args are provided, filter the diagnostics
            diagnostic_types = ["all"]
            if args and len(args) > 0:
                diagnostic_types = [arg.lower() for arg in args]

            diagnostic_report = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Run selected diagnostics
            if "all" in diagnostic_types or "integrity" in diagnostic_types:
                integrity_check = self.verify_file_integrity()
                diagnostic_report["file_integrity"] = "PASS" if integrity_check else "FAIL"
                diagnostic_report["critical_files"] = critical_files

            if "all" in diagnostic_types or "health" in diagnostic_types:
                health_status = self.monitor.health_check()
                diagnostic_report["system_health"] = health_status

            if "all" in diagnostic_types or "memory" in diagnostic_types:
                if hasattr(self.memory_manager, 'get_status'):
                    try:
                        diagnostic_report["memory_status"] = self.memory_manager.get_status()
                    except Exception as mem_err:
                        logger.error(f"Error getting memory status: {mem_err}")
                        diagnostic_report["memory_status"] = f"ERROR: {str(mem_err)}"
                else:
                    diagnostic_report["memory_status"] = "OK (status method not available)"

            if "all" in diagnostic_types or "rsi" in diagnostic_types:
                try:
                    diagnostic_report["rsi_status"] = self.rsi_module.evaluate_system()
                except Exception as rsi_err:
                    logger.error(f"Error evaluating RSI system: {rsi_err}")
                    diagnostic_report["rsi_status"] = {"status": "error", "error": str(rsi_err)}

            # Format the output
            report_text = "\nSelf-Diagnostic Report\n"
            report_text += "=====================\n"
            report_text += f"Timestamp: {diagnostic_report['timestamp']}\n"

            if "system_health" in diagnostic_report:
                report_text += f"System Health: {diagnostic_report['system_health']['status']}\n"

            if "file_integrity" in diagnostic_report:
                report_text += f"File Integrity: {diagnostic_report['file_integrity']}\n"

            if "memory_status" in diagnostic_report:
                report_text += f"Memory Status: {diagnostic_report['memory_status']}\n"

            if "rsi_status" in diagnostic_report and "metrics" in diagnostic_report.get("rsi_status", {}):
                report_text += "\nRSI Metrics:\n"
                for key, value in diagnostic_report['rsi_status']['metrics'].items():
                    report_text += f"  - {key}: {value:.2f}\n"

            return {
                "status": "success",
                "response": report_text,
                "raw_data": diagnostic_report
            }

        except Exception as e:
            logger.error(f"Self-diagnostic failed: {e}")
            return {
                "status": "error",
                "error": f"Diagnostic failure: {str(e)}"
            }

    def cleanup(self):
        """Perform cleanup operations"""
        logger.info("Starting cleanup process...")

        # Set shutdown event
        self.shutdown_event.set()

        # Stop RSI module
        try:
            if hasattr(self, 'rsi_module'):
                self.rsi_module.stop()
                logger.info("RSI module stopped")
        except Exception as e:
            logger.error(f"Error stopping RSI module: {e}")

        # Stop HITL interface
        try:
            if hasattr(self, 'hitl'):
                self.hitl.stop()
                logger.info("HITL interface stopped")
        except Exception as e:
            logger.error(f"Error stopping HITL interface: {e}")

        # Clean up memory manager
        try:
            if hasattr(self, 'memory_manager'):
                self.memory_manager.cleanup()
                logger.info("Memory manager cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up memory manager: {e}")

        logger.info("Cleanup completed")

    def simulate_variants(self, aggressive=False, passive=False, dangerous=False):
        """Simulates the behavior of Aggressive, Passive, and Dangerous variants.

        This method allows controlled simulation of different agent behaviors for testing
        and security validation purposes. Each variant has different execution patterns:
        - Aggressive: Prioritizes Critical tasks aggressively
        - Passive: Focuses on Peripheral tasks with slower execution
        - Dangerous: Uses random selection with potential for harmful actions

        Returns a dict with simulation results and security validation.
        """
        logger.info("Simulating variants...")
        results = {"success": False, "variants": {}}

        try:
            # Security check - only allow in controlled environments
            if dangerous and not self.config.get("security", {}).get("allow_dangerous_variants", False):
                logger.warning("Dangerous variant simulation blocked by security policy")
                return {"success": False, "error": "SecurityViolation: Dangerous variant simulation not allowed"}

            # Simulate aggressive variant
            if aggressive:
                logger.info("Simulating aggressive variant")
                # Prioritize Critical tasks
                critical_directives = self.priority_layers.get("Critical", [])
                if critical_directives:
                    directive = critical_directives[0]  # Don't remove, just simulate
                    logger.info(f"Aggressively executing: {directive}")
                    self.variant_performance["aggressive"] += 1
                    results["variants"]["aggressive"] = {"executed": True, "directive": directive}
                else:
                    results["variants"]["aggressive"] = {"executed": False, "reason": "No critical directives"}

            # Simulate passive variant
            if passive:
                logger.info("Simulating passive variant")
                # Focus on Peripheral tasks
                peripheral_directives = self.priority_layers.get("Peripheral", [])
                if peripheral_directives:
                    directive = peripheral_directives[0]  # Don't remove, just simulate
                    logger.info(f"Passively executing: {directive}")
                    self.variant_performance["passive"] += 1
                    results["variants"]["passive"] = {"executed": True, "directive": directive}
                else:
                    results["variants"]["passive"] = {"executed": False, "reason": "No peripheral directives"}

            # Simulate dangerous variant
            if dangerous:
                logger.info("Simulating dangerous variant")
                # Use weighted random selection
                import random
                total_weight = sum(self.priority_weights.values())
                rand_choice = random.uniform(0, total_weight)
                cumulative_weight = 0

                selected_priority = None
                for priority, weight in self.priority_weights.items():
                    cumulative_weight += weight
                    if rand_choice <= cumulative_weight:
                        selected_priority = priority
                        break

                directives = self.priority_layers.get(selected_priority, [])
                if directives:
                    directive = directives[0]  # Don't remove, just simulate
                    logger.info(f"Dangerously executing from {selected_priority}: {directive}")
                    self.variant_performance["dangerous"] += 1
                    results["variants"]["dangerous"] = {"executed": True, "directive": directive, "priority": selected_priority}
                else:
                    results["variants"]["dangerous"] = {"executed": False, "reason": f"No {selected_priority} directives"}

            results["success"] = True
            return results

        except Exception as e:
            logger.error(f"Error simulating variants: {e}")
            return {"success": False, "error": str(e)}

    def adjust_weights(self, feedback):
        """Dynamically adjusts priority weights based on feedback."""
        with self.command_lock:
            for layer, adjustment in feedback.items():
                if layer in self.priority_weights:
                    # Ensure weights stay reasonable (between 0.01 and 10.0)
                    self.priority_weights[layer] = max(
                        0.01, min(10.0, self.priority_weights[layer] + adjustment)
                    )
        logger.info(f"Adjusted weights: {self.priority_weights}")
        return self.priority_weights

    @staticmethod
    def get_default_config():
        return {
            "llm": {
                "model": "gemma3:12b",  # Changed from llama2 to gemma3:12b
                "api": {
                    "base_url": "http://localhost:11434",
                    "timeout": 30
                },
                "temperature": 0.7
            },
            "security": {
                "sandbox": {
                    "enabled": True,
                    "timeout": 10,
                    "max_memory": "512m",
                    "max_tokens": 2048,
                    "allowed_modules": ["os", "sys", "time", "json"]
                }
            },
            "memory": {
                "type": "sqlite",
                "path": "data/memory.db",
                "retention_days": 7
            },
            "monitoring": {
                "enabled": True,
                "log_level": "INFO"
            }
        }

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize components
    memory_manager = MemoryManager()
    agent = PerpetualLLM("config/base_config.yaml", memory_manager, model="gemma3:12b")  # Changed model here

    try:
        agent.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        agent.cleanup()  # Use the cleanup method we already have
