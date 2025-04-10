import sched
import time
import threading
import logging

# Configure logging for the system task manager.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("system_task_manager.log")],
)
logger = logging.getLogger("SystemTaskManager")


class SystemTaskManager:
    def __init__(self):
        # Create a scheduler using time.time and time.sleep.
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.lock = threading.Lock()
        self.paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused.
        self.tasks = {}  # Dictionary to keep track of scheduled tasks.
        self.running = False
        self.scheduler_thread = None

    def add_task(self, task_name, task_func, delay, priority=1, args=(), kwargs=None):
        """
        Schedule a new task to be executed after a given delay.
        :param task_name: A unique name for the task.
        :param task_func: The function to be executed.
        :param delay: Delay in seconds before execution.
        :param priority: Priority of the task (lower numbers run first).
        :param args: Positional arguments for the task function.
        :param kwargs: Keyword arguments for the task function.
        """
        if kwargs is None:
            kwargs = {}
        with self.lock:
            event = self.scheduler.enter(
                delay,
                priority,
                self._task_wrapper,
                argument=(task_name, task_func, args, kwargs),
            )
            self.tasks[task_name] = event
            logger.info("Task '%s' scheduled to run in %d seconds.", task_name, delay)

    def _task_wrapper(self, task_name, task_func, args, kwargs):
        """
        A wrapper function that waits if the system is paused and then runs the task.
        """
        # Wait until the system is unpaused.
        self.pause_event.wait()
        logger.info("Executing task '%s'.", task_name)
        try:
            task_func(*args, **kwargs)
            logger.info("Task '%s' completed successfully.", task_name)
        except Exception as e:
            logger.error("Error executing task '%s': %s", task_name, e)
        finally:
            with self.lock:
                if task_name in self.tasks:
                    del self.tasks[task_name]

    def remove_task(self, task_name):
        """
        Remove a scheduled task by name.
        """
        with self.lock:
            if task_name in self.tasks:
                try:
                    self.scheduler.cancel(self.tasks[task_name])
                    logger.info("Task '%s' canceled.", task_name)
                except Exception as e:
                    logger.error("Error canceling task '%s': %s", task_name, e)
                del self.tasks[task_name]

    def run(self):
        """
        Start running the scheduler in a separate thread.
        """
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler, daemon=True
            )
            self.scheduler_thread.start()
            logger.info("System Task Manager started.")

    def _run_scheduler(self):
        """
        Continuously run the scheduler.
        """
        while self.running:
            try:
                self.scheduler.run(blocking=False)
            except Exception as e:
                logger.error("Error in scheduler loop: %s", e)
            time.sleep(1)  # Adjust this sleep time as needed.

    def pause(self):
        """
        Pause the task scheduler (HITL intervention).
        """
        self.paused = True
        self.pause_event.clear()
        logger.info("System Task Manager paused for human intervention.")

    def resume(self):
        """
        Resume the task scheduler.
        """
        self.paused = False
        self.pause_event.set()
        logger.info("System Task Manager resumed.")

    def stop(self):
        """
        Stop the scheduler and terminate the scheduler thread.
        """
        self.running = False
        # Resume if paused so that _run_scheduler can exit.
        self.pause_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("System Task Manager stopped.")


# Example tasks for demonstration purposes.
def task_rsi_cycle():
    logger.info("Performing RSI cycle (simulated work)...")
    time.sleep(0.5)  # Simulate some processing time.
    logger.info("RSI cycle completed.")


def task_memory_checkpoint():
    logger.info("Performing Memory Checkpoint (simulated work)...")
    time.sleep(0.5)
    logger.info("Memory checkpoint completed.")


def task_self_diagnostic():
    logger.info("Running Self-Diagnostic (simulated work)...")
    time.sleep(0.5)
    logger.info("Self-Diagnostic completed. All systems nominal.")


# Test hook to demonstrate usage.
if __name__ == "__main__":
    stm = SystemTaskManager()
    stm.run()

    # Schedule some tasks.
    stm.add_task("RSI_Cycle", task_rsi_cycle, delay=5)
    stm.add_task("Memory_Checkpoint", task_memory_checkpoint, delay=10)
    stm.add_task("Self_Diagnostic", task_self_diagnostic, delay=15)

    # Demonstrate pause and resume.
    time.sleep(7)
    stm.pause()
    logger.info("Manually paused the task manager. (Simulating human intervention)")
    time.sleep(5)
    stm.resume()

    # Let the scheduler run for a while.
    time.sleep(20)
    stm.stop()
