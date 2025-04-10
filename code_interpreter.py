import multiprocessing
import time
import logging
import io
import contextlib

# Configure logging for both console and a file.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("code_interpreter.log")],
)
logger = logging.getLogger("CodeInterpreter")

# Define a set of safe built-in functions.
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
    # Extend with additional safe functions if needed.
}


def interpreter_worker(code, return_queue):
    """
    Execute the provided multi-line code snippet in a restricted environment.
    Captures standard output and error messages.
    """
    try:
        # Create StringIO buffers to capture output.
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Set up a restricted global namespace with safe built-ins.
        restricted_globals = {"__builtins__": SAFE_BUILTINS}
        local_vars = {}

        # Redirect stdout and stderr.
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(
            stderr_capture
        ):
            exec(code, restricted_globals, local_vars)

        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()
        return_queue.put(("success", output, errors))
    except Exception as e:
        return_queue.put(("error", "", str(e)))


class CodeInterpreter:
    """
    A Code Interpreter that safely executes Python code snippets in a sandboxed subprocess.
    Captures both output and error messages while enforcing a timeout.
    """

    def __init__(self, timeout=5):
        self.timeout = timeout

    def execute(self, code):
        """
        Execute the given code snippet.

        :param code: str, Python code to execute.
        :return: Tuple (status, output, error_message) where status can be "success", "error", or "timeout".
        """
        manager = multiprocessing.Manager()
        return_queue = manager.Queue()
        process = multiprocessing.Process(
            target=interpreter_worker, args=(code, return_queue)
        )
        process.start()
        process.join(self.timeout)

        if process.is_alive():
            process.terminate()
            process.join()
            logger.error(
                "Code interpretation timed out after %s seconds.", self.timeout
            )
            return ("timeout", "", "Execution timed out")

        if not return_queue.empty():
            status, output, error_message = return_queue.get()
            logger.info(
                "Code interpretation result: %s\nOutput:\n%s\nError:\n%s",
                status,
                output,
                error_message,
            )
            return (status, output, error_message)

        logger.error("Code interpretation produced no output.")
        return ("error", "", "No output from interpreter.")


if __name__ == "__main__":
    interpreter = CodeInterpreter(timeout=3)
    test_code = """
for i in range(3):
    print("Hello, world!", i)
"""
    status, output, error_message = interpreter.execute(test_code)
    logger.info(
        "Final interpreter status: %s, output: %s, error: %s",
        status,
        output,
        error_message,
    )
