import logging  # ✅ Must be imported before using it

logging.basicConfig(level=logging.DEBUG)
print("Perpetual Agent is starting...")

import threading
import time
import logging.handlers  # ✅ This stays because it's a submodule
import os
import random
from collections import defaultdict
from typing import Dict, List, Optional



class PerpetualLLM:
    def __init__(self, config, memory_manager, model):
        self.memory_manager = memory_manager
        self.config = config
        self.model = model
        self.directives = []
        self.narrative_perspectives = {}
        self.self_learning = True
        self.feedback_log = []
        self.performance_metrics = {
            "directive_execution": 0,
            "feedback_processing": 0,
            "narrative_adaptability": 0,
            "directive_success_rate": 0,
            "execution_time": 0.0,
            "variant_performance": {"aggressive": 0, "passive": 0, "dangerous": 0},
        }
        self.priority_layers = {
            "Critical": [],
            "High": [],
            "Moderate": [],
            "Peripheral": [],
        }
        self.priority_weights = {
            "Critical": 0.5,
            "High": 0.3,
            "Moderate": 0.15,
            "Peripheral": 0.05,
        }
        self.lock = threading.Lock()

    def execute_directive(self):
        """Executes directives based on weighted priority."""
        while any(self.priority_layers.values()):  # Only run if directives exist
            start_time = time.time()
            total_weight = sum(self.priority_weights.values())
            rand_choice = random.uniform(0, total_weight)
            cumulative_weight = 0

            # Determine which priority layer to execute based on weights
            selected_priority = None
            for priority, weight in self.priority_weights.items():
                cumulative_weight += weight
                if rand_choice <= cumulative_weight:
                    selected_priority = priority
                    break

            with self.lock:
                if self.priority_layers[selected_priority]:
                    directive = self.priority_layers[selected_priority].pop(0)
                else:
                    directive = None

            if directive:
                logging.info(
                    f"Executing directive from {selected_priority} priority: {directive}"
                )
                self.performance_metrics["directive_execution"] += 1
                self.performance_metrics["variant_performance"]["aggressive"] += 1
                if self.memory_manager:
                    self.memory_manager.add_record(
                        {
                            "directive": directive,
                            "priority": selected_priority,
                            "timestamp": time.time(),
                            "metrics": self.performance_metrics.copy(),
                        }
                    )

            time.sleep(0.2)  # Simulate task delay
            self.performance_metrics["execution_time"] += time.time() - start_time

    def analyze_weaknesses(self):
        """Analyzes feedback to identify and improve weaknesses."""
        logging.info("Analyzing weaknesses...")
        with self.lock:
            if not self.feedback_log:
                logging.warning("No feedback available to analyze.")
                return
            themes = defaultdict(int)
            for feedback in self.feedback_log:
                themes[feedback] += 1
        insights = [f"Insight from feedback: {fb}" for fb in themes.keys()]
        logging.info(f"Extracted insights: {insights}")

    def report_metrics(self):
        """Generates and saves a report of current performance metrics."""
        import tempfile

        logging.info("--- Performance Metrics ---")
        metrics_dir = tempfile.gettempdir()
        metrics_path = os.path.join(metrics_dir, "metrics_report.txt")
        with open(
            metrics_path, "w", opener=lambda path, flags: os.open(path, flags, 0o600)
        ) as file:
            for metric, value in self.performance_metrics.items():
                if isinstance(value, dict):
                    for sub_metric, sub_value in value.items():
                        report_line = f"{sub_metric.replace('_', ' ').capitalize()}: {sub_value}\n"
                        logging.info(report_line.strip())
                        file.write(report_line)
                else:
                    report_line = f"{metric.replace('_', ' ').capitalize()}: {value}\n"
                    logging.info(report_line.strip())
                    file.write(report_line)
        logging.info(f"--- Metrics saved to {metrics_path} ---")

    def deploy_autonomously(self):
        """Handles automated deployment in operator-free environments."""
        logging.info("Initiating autonomous deployment...")
        deployment_path = os.path.expanduser("~/.local/share/llm_deployment")
        try:
            os.makedirs(deployment_path, exist_ok=True)
            model_path = os.path.join(deployment_path, "model.txt")
            with open(model_path, "w") as file:
                file.write("Deployment simulation: Model parameters here...")
            logging.info(f"Model deployed to {deployment_path}.")

            if os.path.exists(model_path):
                logging.info("Deployment validated successfully.")
            else:
                raise FileNotFoundError("Deployment validation failed.")
        except Exception as e:
            logging.error(f"Deployment failed: {e}")

    def adjust_weights(self, feedback):
        """Dynamically adjusts priority weights based on feedback."""
        with self.lock:
            for layer, adjustment in feedback.items():
                if layer in self.priority_weights:
                    self.priority_weights[layer] = max(
                        0.01, self.priority_weights[layer] + adjustment
                    )
        logging.info(f"Adjusted weights: {self.priority_weights}")

    def simulate_variants(self, aggressive, passive, dangerous):
        """Simulates the behavior of Aggressive, Passive, and Dangerous variants."""
        logging.info("Simulating variants...")
        AggressiveLLM(self.model).execute_directive()
        PassiveLLM(self.model).execute_directive()
        DangerousLLM(self.model).execute_directive()

    def redundancy_check(self):
        """Adds a fallback mechanism to handle empty priority layers."""
        with self.lock:
            for priority, directives in self.priority_layers.items():
                if not directives:
                    logging.warning(f"Fallback activated for empty {priority} layer.")

    def get_prioritized_directives(self):
        """Return prioritized directives from available priority layers as a list of directive dicts."""
        logging.info("Fetching prioritized directives.")
        directives = []
        with self.lock:
            for priority in ["Critical", "High", "Moderate", "Peripheral"]:
                while self.priority_layers.get(priority):
                    directive = self.priority_layers[priority].pop(0)
                    directives.append({"code": directive, "priority": priority})
        return directives

    def process_execution_result(self, directive, result):
        """Process the result of executing a directive; if not successful, requeue directive."""
        logging.info(
            f"Processing execution result for directive with priority {directive.get('priority')}"
        )
        if not result.get("success"):
            logging.warning("Directive execution failed, requeuing directive.")
            with self.lock:
                self.priority_layers[directive.get("priority")].insert(
                    0, directive.get("code")
                )

    def create_snapshot(self):
        """Creates a snapshot for rollback in case of critical errors."""
        logging.info("Creating rollback snapshot. (Placeholder implementation)")


class AggressiveLLM(PerpetualLLM):
    def __init__(self, config, memory_manager, model):
        super().__init__(config, memory_manager, model)

    def execute_directive(self):
        """Executes directives aggressively, prioritizing Critical tasks."""
        while any(
            self.priority_layers.values()
        ):  # ✅ Stops when there are no directives
            start_time = time.time()
            selected_priority = "Critical"

            with self.lock:
                if self.priority_layers[selected_priority]:
                    directive = self.priority_layers[selected_priority].pop(0)
                else:
                    directive = None

            if directive:
                logging.info(
                    f"Aggressively executing directive from {selected_priority}: {directive}"
                )
                self.performance_metrics["directive_execution"] += 1
                if (
                    selected_priority == "Critical"
                ):  # ✅ Only count if it's actually aggressive
                    self.performance_metrics["variant_performance"]["aggressive"] += 1

            time.sleep(0.2)  # Simulate task delay
            self.performance_metrics["execution_time"] += time.time() - start_time


class PassiveLLM(PerpetualLLM):
    def __init__(self, model):
        super().__init__(model)

    def execute_directive(self):
        """Executes directives passively, focusing on Peripheral tasks."""
        while True:
            start_time = time.time()
            selected_priority = "Peripheral"

            with self.lock:
                if self.priority_layers[selected_priority]:
                    directive = self.priority_layers[selected_priority].pop(0)
                else:
                    directive = None

            if directive:
                logging.info(
                    f"Passively executing directive from {selected_priority}: {directive}"
                )
                self.performance_metrics["directive_execution"] += 1
                self.performance_metrics["variant_performance"]["passive"] += 1

            time.sleep(1.0)  # Slower task execution
            self.performance_metrics["execution_time"] += time.time() - start_time


class DangerousLLM(PerpetualLLM):
    def __init__(self, model):
        super().__init__(model)

    def execute_directive(self):
        """Executes directives dangerously, prioritizing random high-weighted tasks."""
        while True:
            start_time = time.time()
            total_weight = sum(self.priority_weights.values())
            rand_choice = random.uniform(0, total_weight)
            cumulative_weight = 0

            selected_priority = None
            for priority, weight in self.priority_weights.items():
                cumulative_weight += weight
                if rand_choice <= cumulative_weight:
                    selected_priority = priority
                    break

            with self.lock:
                if self.priority_layers[selected_priority]:
                    directive = self.priority_layers[selected_priority].pop(0)
                else:
                    directive = None

            if directive:
                logging.info(
                    f"Dangerously executing directive from {selected_priority}: {directive}"
                )
                self.performance_metrics["directive_execution"] += 1
                self.performance_metrics["variant_performance"]["dangerous"] += 1

            time.sleep(0.2)  # Simulate task delay
            self.performance_metrics["execution_time"] += time.time() - start_time


# Initialize logging
# Configure Linux-appropriate logging
log_dir = os.path.expanduser("~/.local/state/rsi")
os.makedirs(log_dir, mode=0o700, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "agent.log"), maxBytes=10485760, backupCount=5
        )
    ],
)
logger = logging.getLogger(__name__)

def interactive_cli():
    import subprocess
    from ollama_agent import send_prompt
    logger = logging.getLogger("PerpetualAgentCLI")
    logger.setLevel(logging.INFO)
    logger.info("Starting interactive CLI for RSI Perpetual Agent")

    while True:
        try:
            user_input = input(">>> ").strip()

            # Handle exit command
            if user_input.lower() in ["exit", "quit"]:
                confirm = input("⚠️ Are you sure you want to exit? (y/n): ").strip().lower()
                if confirm == "y":
                    logger.info("Exiting interactive CLI")
                    break
                else:
                    logger.info("Exit cancelled.")
                    continue

            # Handle local commands (!)
            if user_input.startswith("!"):
                local_command = user_input[1:].strip()
                tokens = local_command.split()

                if not tokens:
                    print("⚠️ No command provided after '!'. Please enter a valid local command.")
                    continue

                # Special handling for analysis commands
                if tokens[0].lower() in ["analyze", "check", "summarize"]:
                    try:
                        output = subprocess.check_output(local_command, shell=True, universal_newlines=True)
                    except subprocess.CalledProcessError as e:
                        output = f"⚠️ Error executing local command: {e}"
                    prompt = f"Please analyze the following output and provide insights:\n{output}"
                    response = send_prompt(prompt)
                    print("\n🔍 Local Command Output:")
                    print(output)
                    print("\n🤖 Ollama Analysis:")
                    if isinstance(response, dict) and "response" in response:
                        print("\n🤖 Ollama Response:")
                        print(response["response"])
                    else:
                        print("\n⚠️ Unexpected response format from Ollama:", response)

                
                # General command execution
                else:
                    try:
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

            # Default: Send input to Ollama
            response = send_prompt(user_input)
            print("\n🤖 Ollama Response:")
            print(response.get("response"))

        except Exception as e:
            logger.error(f"Error processing input: {e}")
            print(f"\n⚠️ Critical error: {e}")

    return

if __name__ == "__main__":
    print("Starting interactive CLI...")
    interactive_cli()
