import time
import logging
from consolidated_code_analysis import ConsolidatedCodeAnalysis
from system_task_manager import SystemTaskManager

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("hitl_interface.log")],
)
logger = logging.getLogger("HITLInterface")

class HITLInterface:
    def __init__(self, config=None):
        self.config = config or {}
        self.task_manager = SystemTaskManager()
        self.running = False
        logger.info("HITL Interface initialized")

    async def alert_degraded_state(self, health_status):
        """Alert about degraded system state"""
        logger.warning(f"System in degraded state: {health_status}")

        # In a real implementation, this would send notifications
        # via email, SMS, or other channels asynchronously

        # Simulate async operation
        import asyncio
        await asyncio.sleep(0.1)

        # Log the alert to a file for tracking
        try:
            with open("alerts.log", "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ALERT: System in degraded state: {health_status}\n")
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")

        return True

    def start(self):
        """Start the HITL interface"""
        self.running = True
        logger.info("HITL Interface started")

    def stop(self):
        """Stop the HITL interface"""
        self.running = False
        logger.info("HITL Interface stopped")

    def review_code_changes(self):
        """Review code changes"""
        try:
            analyzer = ConsolidatedCodeAnalysis()
            report = analyzer.generate_aggregated_report()
            logger.info(f"Code review completed with {len(report.get('diff_report', {}))} differences found")
            return True
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            return False

def hitl_command_loop(task_manager):
    """Command loop for HITL interface"""
    while True:
        cmd = input("HITL> ").strip().lower()
        if cmd == "help":
            print("\nAvailable commands:")
            print("  reset     - Restart the system task manager")
            print("  status    - Show currently scheduled tasks")
            print("  review    - Run code analysis and review changes")
            print("  help      - Display this help message")
            print("  exit      - Exit the HITL interface and stop the system")
        elif cmd == "exit":
            logger.info("Exiting HITL interface. Stopping system task manager.")
            task_manager.stop()
            break
        else:
            print("Unknown command. Type 'help' for available commands.")

def main():
    stm = SystemTaskManager()
    stm.run()

    stm.add_task(
        "RSI_Cycle", lambda: logger.info("Simulated RSI cycle executed."), delay=5
    )
    stm.add_task(
        "Memory_Checkpoint",
        lambda: logger.info("Simulated Memory Checkpoint executed."),
        delay=10,
    )
    stm.add_task(
        "Self_Diagnostic",
        lambda: logger.info("Simulated Self-Diagnostic executed."),
        delay=15,
    )

    hitl_command_loop(stm)

if __name__ == "__main__":
    main()
