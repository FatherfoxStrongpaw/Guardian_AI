import logging
import json
import time
import os
from typing import Dict, Optional, Union, List
from pathlib import Path
from threading import Event, Lock
from datetime import datetime
import hashlib
import asyncio
import yaml
from dataclasses import dataclass

from rsi_module import RSIModule
from ollama_agent import OllamaAgent
from memory_manager import MemoryManager
from sandbox_executor import SandboxExecutor
from hitl_interface import HITLInterface

logger = logging.getLogger(__name__)

@dataclass
class SecurityContext:
    """Security context for command execution"""
    allowed_modules: List[str]
    max_tokens: int
    timeout: int
    sandbox_enabled: bool = True

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
        
        return SecurityContext(
            trust_level=trust_level,
            requires_hitl=requires_hitl,
            allowed_modules=self.config["security"]["sandbox"]["allowed_modules"],
            execution_timeout=self.config["security"]["sandbox"]["timeout"],
            memory_limit=self.config["security"]["sandbox"]["max_memory"]
        )

class SystemMonitor:
    """Monitors system health and performance"""
    def __init__(self):
        self.start_time = datetime.now()
        self.command_history = []
        self.error_count = 0
        self.last_health_check = None
        
    async def health_check(self) -> Dict[str, Union[str, int, float]]:
        """Perform system health check"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        error_rate = self.error_count / len(self.command_history) if self.command_history else 0
        
        return {
            "status": "healthy" if error_rate < 0.1 else "degraded",
            "uptime": uptime,
            "error_rate": error_rate,
            "commands_processed": len(self.command_history),
            "last_check": datetime.now().isoformat()
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
        
        # Initialize components with enhanced security
        self.memory_manager = memory_manager
        self.sandbox = SandboxExecutor(self.config)
        self.hitl = HITLInterface(self.config)
        
        # Initialize RSI module with security context
        self.rsi_module = RSIModule(
            config_file=config_path,
            memory_manager_instance=memory_manager,
            sandbox_executor=self.sandbox
        )
        
        # Initialize Ollama agent
        self.ollama = OllamaAgent(
            model=self.config.get("llm", {}).get("model", model),
            base_url=self.config.get("llm", {}).get("api", {}).get("base_url", "http://localhost:11434")
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

    async def handle_degraded_state(self, health_status: dict):
        """Handle degraded system state"""
        logger.warning("System in degraded state - initiating recovery")
        
        # Notify HITL
        await self.hitl.alert_degraded_state(health_status)
        
        # Attempt self-healing
        try:
            await self.rsi_module.self_heal()
        except Exception as e:
            logger.error(f"Self-healing failed: {e}")

    def verify_file_integrity(self) -> bool:
        """Verify integrity of critical files"""
        critical_files = [
            "perpetual_agent.py",
            "rsi_module.py", 
            "sandbox_executor.py",
            "hitl_interface.py"
        ]
        
        for file in critical_files:
            try:
                with open(file, 'rb') as f:
                    content = f.read()
                    current_hash = hashlib.sha256(content).hexdigest()
                    
                    # Compare with stored hash
                    stored_hash = self.memory_manager.get_hash(file)
                    if stored_hash and stored_hash != current_hash:
                        logger.error(f"Integrity check failed for {file}")
                        return False
                        
                    # Store new hash if none exists
                    if not stored_hash:
                        self.memory_manager.store_hash(file, current_hash)
                        
            except Exception as e:
                logger.error(f"Failed to verify {file}: {e}")
                return False
                
        return True

    async def process_input(self, user_input: str) -> Dict:
        """Process user input and execute appropriate action"""
        try:
            if user_input.startswith("!"):
                return await self.handle_command(user_input[1:])
            
            response = await self.ollama.generate_response(user_input)
            return {"status": "success", "response": response}
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return {"status": "error", "error": str(e)}

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
            "consider_self": self.run_self_diagnostic  # Add new command
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
            metrics = self.monitor.health_check()
            return {"status": "success", "response": metrics}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_system_status(self, args: List[str]) -> Dict:
        """Get current system status"""
        try:
            health = await self.monitor.health_check()
            metrics = self.metrics.copy()
            metrics.update(health)
            return {"status": "success", "response": metrics}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run(self):
        """Main execution loop"""
        self.running = True
        print("\n🤖 RSI Agent initialized. Type !help for commands.")
        
        while self.running:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    self.running = False
                    continue
                    
                result = asyncio.run(self.process_input(user_input))
                
                if result["status"] == "success":
                    print("\n🤖 Response:", result["response"])
                else:
                    print("\n⚠️ Error:", result["error"])
                    
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"\n⚠️ Unexpected error: {e}")

    async def show_help(self, args: List[str] = None) -> Dict:
        """Show available commands and usage"""
        help_text = """
Available Commands:
-----------------
!rsi <command>    : Execute RSI-related operations
!analyze <input>  : Analyze system output or behavior
!system <command> : Execute system commands (sandboxed)
!help             : Show this help message
!status           : Show system status
!consider_self    : Run system self-diagnostics
"""
        print(help_text)
        return {"status": "success", "response": "Help displayed"}

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
            
            # Run diagnostics
            integrity_check = self.verify_file_integrity()
            health_status = await self.monitor.health_check()
            
            diagnostic_report = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "system_health": health_status,
                "file_integrity": "PASS" if integrity_check else "FAIL",
                "critical_files": critical_files,
                "memory_status": self.memory_manager.get_status() if hasattr(self.memory_manager, 'get_status') else "OK",
                "rsi_status": self.rsi_module.evaluate_system()
            }
            
            # Format the output
            report_text = "\nSelf-Diagnostic Report\n"
            report_text += "=====================\n"
            report_text += f"Timestamp: {diagnostic_report['timestamp']}\n"
            report_text += f"System Health: {diagnostic_report['system_health']['status']}\n"
            report_text += f"File Integrity: {diagnostic_report['file_integrity']}\n"
            report_text += f"Memory Status: {diagnostic_report['memory_status']}\n"
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
        self.shutdown_event.set()
        self.rsi_module.stop()
        self.memory_manager.cleanup()
        logger.info("Cleanup completed")

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
