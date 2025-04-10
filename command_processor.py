import logging
from rsi_module import RSIModule

class CommandProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rsi_module = RSIModule()

    def process_command(self, command: str) -> str:
        """Process commands directly without LLM intervention"""
        if command.startswith("!rsi"):
            return self.process_rsi_command(command[5:].strip())  # Remove !rsi prefix
        return None  # Let other commands go to LLM

    def process_rsi_command(self, directive: str) -> str:
        try:
            if directive.startswith("execute_task"):
                task_name = directive.split("'")[1] if "'" in directive else directive.split('"')[1]
                
                # Get baseline metrics
                before_metrics = self.rsi_module.evaluate_system()
                
                # Execute the optimization
                self.rsi_module.execute_task(task_name)
                
                # Get updated metrics
                after_metrics = self.rsi_module.evaluate_system()
                
                return (
                    f"Executed task: {task_name}\n"
                    f"Before optimization:\n"
                    f"  - Error rate: {before_metrics['error_rate']:.3f}\n"
                    f"  - Response time: {before_metrics['response_time']:.3f}\n"
                    f"After optimization:\n"
                    f"  - Error rate: {after_metrics['error_rate']:.3f}\n"
                    f"  - Response time: {after_metrics['response_time']:.3f}"
                )
            
            elif directive == "self_improve":
                self.rsi_module.self_improve()
                return "Completed self-improvement cycle"
            
            else:
                return f"Unknown RSI directive: {directive}"
                
        except Exception as e:
            self.logger.error(f"Error processing RSI command: {e}")
            return f"Failed to process RSI command: {str(e)}"