import json
import logging
import os
import random
import time
import traceback
from threading import Thread, Event

# Import the MemoryManager class from your memory_manager.py file.
# Adjust the import if your file/module name differs.
from memory_manager import MemoryManager
from perpetual_agent import PerpetualLLM
import hashlib
import hmac

# Configure logging for both console and a file.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("rsi_module.log")],
)

logger = logging.getLogger("RSIModule")


class RSIModule:
    def __init__(
        self,
        config_file="config.json",
        memory_manager_instance=None,
        sandbox_executor=None,
    ):
        self.sandbox_executor = sandbox_executor
        self.config_file = config_file
        self.config = {}
        self.last_config_modified = 0
        self.loop_counter = 0
        self.shutdown_event = Event()
        self.load_config()
        self.loop_limit = self.config.get("loop_limit", 10000)
        self.memory_manager = memory_manager_instance

        # Initialize PerpetualLLM with shared dependencies
        self.agent = PerpetualLLM(
            config=self.config,
            memory_manager=self.memory_manager,
            model=self.config.get("llm_model", "llama2"),
        )

    def load_config(self):
        """Load configuration parameters from a JSON file and update if modified."""
        try:
            modified_time = os.path.getmtime(self.config_file)
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
            self.last_config_modified = modified_time
            logger.info("Configuration loaded/reloaded successfully.")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"❌ Config file error: {e}. Restoring default settings.")
            self.config = {
                "error_threshold": 0.1,
                "response_time_threshold": 0.5,
                "check_interval": 10,
                "loop_limit": 10000,
            }
            self.save_config()

    def save_config(self):
        """Persist the current configuration back to the JSON file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully.")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def evaluate_system(self):
        """
        Evaluate the current system performance.
        Here, we simulate performance metrics with dynamic values.
        """
        performance_metrics = {
            "error_rate": round(
                random.uniform(0.0, 0.15), 3
            ),  # Simulate error rate between 0% and 15%
            "response_time": round(
                random.uniform(0.1, 0.8), 3
            ),  # Simulate response time between 0.1s and 0.8s
        }
        logger.info(f"Evaluated performance metrics: {performance_metrics}")
        return performance_metrics

    def improvement_tasks(self, metrics):
        """
        Decide which tasks to run based on the evaluated metrics.
        Logs rationale for each selected task.
        """
        tasks = []
        if metrics["error_rate"] > self.config.get("error_threshold", 0.1):
            tasks.append("optimize_error_handling")
            logger.info(
                "Task selected: optimize_error_handling (error_rate %.3f > threshold %.3f)",
                metrics["error_rate"],
                self.config.get("error_threshold", 0.1),
            )
        if metrics["response_time"] > self.config.get("response_time_threshold", 0.5):
            tasks.append("optimize_response_time")
            logger.info(
                "Task selected: optimize_response_time (response_time %.3f > threshold %.3f)",
                metrics["response_time"],
                self.config.get("response_time_threshold", 0.5),
            )
        return tasks

    def execute_task(self, task):
        """
        Execute task via sandbox with security context
        """
        try:
            if not self.sandbox_executor:
                if task == "optimize_error_handling":
                    logger.warning("Sandbox executor not available; falling back to direct optimize_error_handling execution.")
                    self.optimize_error_handling()
                    return
                elif task == "optimize_response_time":
                    logger.warning("Sandbox executor not available; falling back to direct optimize_response_time execution.")
                    self.optimize_response_time()
                    return
                else:
                    logger.error("Sandbox executor not available and no fallback defined for task: %s", task)
                    raise RuntimeError("Sandbox executor not initialized")

            # Prepare execution environment
            env = {
                "config": self.config,
                "memory_manager": self.memory_manager,
                "logger": logger,
            }

            # Execute in sandbox with timeout
            result = self.sandbox_executor.run_safe(
                code=f"execute_task({task})",
                environment=env,
                timeout=self.config.get("task_timeout", 30),
            )

            if result["success"]:
                logger.info(f"Task completed: {task}")
            else:
                logger.error(f"Task failed: {result['error']}")

        except Exception as e:
            logger.error(f"Task execution error: {str(e)}")
            if self.memory_manager:
                self.memory_manager.add_record({"task": task, "error": str(e)})

    def optimize_error_handling(self):
        """Simulate an improvement in error handling by adjusting the threshold."""
        logger.info("Starting optimization: error handling")
        try:
            # Simulate work.
            current_threshold = self.config.get("error_threshold", 0.1)
            new_threshold = max(0.01, current_threshold * 0.9)
            logger.info(
                f"Optimizing error handling: error_threshold changing from {current_threshold} to {new_threshold}"
            )
            self.config["error_threshold"] = new_threshold
            self.save_config()
        except Exception as e:
            logger.error(f"Error in optimize_error_handling: {e}")

    def optimize_response_time(self):
        """Simulate an improvement in response time handling."""
        logger.info("Starting optimization: response time")
        try:
            time.sleep(1)
            current_threshold = self.config.get("response_time_threshold", 0.5)
            new_threshold = max(0.1, current_threshold * 0.9)
            logger.info(
                f"Optimizing response time: response_time_threshold changing from {current_threshold} to {new_threshold}"
            )
            self.config["response_time_threshold"] = new_threshold
        except Exception as e:
            logger.error(f"Error in optimize_response_time: {e}")

    def self_improve(self):
        """
        The core self-improvement routine:
          1. Reload configuration if updated.
          2. Evaluate system performance.
          3. Determine and execute necessary improvement tasks.
          4. Log and record the improvement cycle via Memory Manager.
          5. Save updated configuration.
        """
        try:
            self.load_config()  # Reload config if updated
            metrics_before = self.evaluate_system()
            tasks = self.improvement_tasks(metrics_before)
            if tasks:
                for task in tasks:
                    self.execute_task(task)
                metrics_after = self.evaluate_system()
                improvement_log = {
                    "metrics_before": metrics_before,
                    "metrics_after": metrics_after,
                    "tasks_executed": tasks,
                    "timestamp": time.time(),
                }
                # Log the improvement cycle to the memory manager, if available.
                if self.memory_manager:
                    self.memory_manager.add_record(improvement_log)
                else:
                    logger.warning(
                        "Memory Manager not set. Improvement cycle not logged to persistent storage."
                    )
                self.save_config()
            else:
                logger.info("No improvements needed at this time.")
        except Exception as e:
            logger.error(f"Error during self-improvement: {e}")
            logger.debug(traceback.format_exc())

    def run_loop(self):
        """
        Enhanced execution loop integrating PerpetualLLM agent:
        1. Load latest config
        2. Get directives from agent
        3. Execute highest priority tasks
        4. Analyze results and improve
        """
        check_interval = self.config.get("check_interval", 10)
        loop_limit = self.config.get("loop_limit", 10000)
        logger.info(
            f"Starting integrated RSI loop with {check_interval}s intervals and loop limit {loop_limit}"
        )

        while not self.shutdown_event.is_set() and self.loop_counter < loop_limit:
            # 🚨 New: Prevent infinite looping if the agent degrades
            if self.agent.performance_metrics.get("directive_success_rate", 1.0) < 0.1:
                logger.warning("⚠️ Loop exit condition met: Success rate too low. Shutting down.")
                break
            
            try:
                # Get agent's prioritized directives
                directives = self.agent.get_prioritized_directives()

                # Execute through sandbox with security constraints if available
                if self.sandbox_executor:
                    for directive in directives:
                        result = self.sandbox_executor.run_safe(
                            code=directive["code"],
                            environment={
                                "config": self.config,
                                "memory": self.memory_manager,
                            },
                        )

                        # Log the executed directive for better tracking
                        logger.info(f"✅ Executed directive: {directive}")

                        # Let agent process results
                        self.agent.process_execution_result(directive, result)

                        # Update local config if modified
                        if "config" in result.get("output", {}):
                            self.config.update(result["output"]["config"])
                            self.save_config()
                else:
                    logging.warning(
                        "⚠️ WARNING: Sandbox executor is missing! Directives are not executing."
                    )

                # Agent self-analysis and improvement
                self.agent.analyze_weaknesses()
                self.agent.report_metrics()

                # Core RSI improvement cycle
                self.self_improve()
                self.loop_counter += 1

                time.sleep(check_interval)

            except Exception as e:
                logger.error(f"Critical loop error: {str(e)}")
                self.agent.create_snapshot()  # Rollback point
                break

        logger.info("Integrated RSI loop terminated")


    def start(self):
        """Start the RSI module in a dedicated background thread."""
        self.thread = Thread(target=self.run_loop, daemon=True)
        self.thread.start()
        logger.info("RSI module started in a background thread.")

    def stop(self):
        """Signal the RSI module to shut down gracefully."""
        self.shutdown_event.set()
        self.thread.join()
        logger.info("RSI module stopped.")


if __name__ == "__main__":
    # For testing purposes, create an instance of MemoryManager and pass it to RSIModule.
    mm = MemoryManager()
    rsi = RSIModule(memory_manager_instance=mm)
    try:
        rsi.start()
        # Keep the main thread alive until a KeyboardInterrupt is received.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down RSI module.")
        rsi.stop()
