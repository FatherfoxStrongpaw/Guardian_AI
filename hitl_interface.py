import json
import time
import logging
import threading
from consolidated_code_analysis import (
    ConsolidatedCodeAnalysis,
)  # Your multi-file analysis module
from system_task_manager import SystemTaskManager  # Your system-level task manager

# Configure logging for the HITL interface.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("hitl_interface.log")],
)
logger = logging.getLogger("HITLInterface")


def review_code_changes():
    """
    Run the consolidated code analysis to generate an aggregated report,
    then interactively review each file that has differences.

    For each file with differences, the diff and dependency information are displayed.
    The user is prompted to approve ('y') or reject ('n') the changes.
    """
    # Instantiate the Consolidated Code Analysis module.
    cca = ConsolidatedCodeAnalysis()
    report = cca.generate_aggregated_report()

    # Print a summary of the aggregated report.
    print("\n=== Aggregated Code Analysis Report ===")
    print(json.dumps(report, indent=4))

    diff_report = report.get("diff_report", {})

    # Iterate over each file with differences.
    for rel_path, diff in diff_report.items():
        if diff:
            print("\n--------------------------------------------------")
            print(f"File: {rel_path}")
            print("Differences:")
            print("\n".join(diff))

            # Show dependency information (if available)
            baseline_deps = report.get("baseline_dependencies", {}).get(rel_path, {})
            staging_deps = report.get("staging_dependencies", {}).get(rel_path, {})
            print("Baseline Dependencies:", json.dumps(baseline_deps, indent=2))
            print("Staging Dependencies:", json.dumps(staging_deps, indent=2))
            print("--------------------------------------------------")

            # Prompt for decision.
            decision = (
                input(f"Approve changes for '{rel_path}'? (y/n): ").strip().lower()
            )
            if decision == "y":
                cca.approve_change(rel_path)
                logger.info("Approved changes for '%s'.", rel_path)
            else:
                cca.reject_change(rel_path)
                logger.info("Rejected changes for '%s'.", rel_path)

    print("\nCode review complete.\n")


def hitl_command_loop(task_manager: SystemTaskManager):
    """
    A command-line HITL loop that allows manual intervention.
    Commands include:
      - pause: Pause system task execution.
      - resume: Resume system task execution.
      - reset: Restart the system task manager.
      - status: Show current scheduled tasks.
      - review: Launch code review via the Consolidated Code Analysis module.
      - diagnostics: Show recent diagnostic logs (if implemented in your centralized diagnostics module).
      - help: List available commands.
      - exit: Exit the HITL interface and stop the system.
    """
    logger.info("HITL interface started. Type 'help' for available commands.")
    while True:
        try:
            cmd = (
                input(
                    "Enter command (pause, resume, reset, status, review, help, exit): "
                )
                .strip()
                .lower()
            )
        except EOFError:
            break

        if cmd == "pause":
            task_manager.pause()
            logger.info("System paused by user.")
        elif cmd == "resume":
            task_manager.resume()
            logger.info("System resumed by user.")
        elif cmd == "reset":
            logger.info("Reset command received. Restarting the system...")
            task_manager.stop()
            time.sleep(1)
            task_manager.run()
            logger.info("System restarted.")
        elif cmd == "status":
            with task_manager.lock:
                tasks = list(task_manager.tasks.keys())
            logger.info("Current scheduled tasks: %s", tasks)
            print("Current scheduled tasks:", tasks)
        elif cmd == "review":
            review_code_changes()
        elif cmd == "diagnostics":
            # Import the necessary functions from your self_diagnostic module.
            from self_diagnostic import run_self_diagnostics, print_diagnostic_report

            # Define a list of critical files to check.
            critical_files = [
                "baseline/module1.py",
                "baseline/module2.py",
                "config.json",
            ]
            diag_report = run_self_diagnostics(critical_files)
            print_diagnostic_report(diag_report)
        elif cmd == "help":
            print("Available commands:")
            print("  pause     - Pause the system task execution")
            print("  resume    - Resume the system task execution")
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
    """
    Main function to initialize the system task manager and launch the HITL command loop.
    """
    # Instantiate your system task manager.
    stm = SystemTaskManager()
    stm.run()

    # Optionally, schedule some example system-level tasks.
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

    # Launch the HITL command loop.
    hitl_command_loop(stm)


if __name__ == "__main__":
    main()
