import logging
import threading


class ListHandler(logging.Handler):
    """
    A logging handler that stores log records in a list.
    Each record is stored as a tuple: (levelno, formatted_message).
    """

    def __init__(self):
        super().__init__()
        self.logs = []
        self.lock = threading.Lock()

    def emit(self, record):
        msg = self.format(record)
        with self.lock:
            self.logs.append((record.levelno, msg))

    def get_logs(self, level=logging.ERROR):
        """
        Return all log messages with a severity equal or above the given level.
        """
        with self.lock:
            return [msg for lvl, msg in self.logs if lvl >= level]

    def clear_logs(self):
        with self.lock:
            self.logs.clear()


class CentralizedDiagnostics:
    """
    Centralized Diagnostics aggregates log records from across the system.
    It provides methods to query error and warning logs, check error thresholds,
    and clear the log store.
    """

    def __init__(self):
        # Create and configure the custom log handler.
        self.handler = ListHandler()
        self.handler.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        self.handler.setFormatter(formatter)

        # Add the handler to the root logger so all modules send their logs here.
        logging.getLogger().addHandler(self.handler)

    def get_error_logs(self):
        """
        Retrieve all error (or higher severity) logs.
        """
        return self.handler.get_logs(logging.ERROR)

    def get_warning_logs(self):
        """
        Retrieve all warning (or higher severity) logs.
        """
        return self.handler.get_logs(logging.WARNING)

    def check_error_threshold(self, threshold=5):
        """
        Check if the number of error logs exceeds the specified threshold.
        If so, log an alert.
        """
        error_logs = self.get_error_logs()
        if len(error_logs) >= threshold:
            alert_msg = (
                f"Error threshold exceeded! {len(error_logs)} errors logged:\n"
                + "\n".join(error_logs)
            )
            logging.getLogger().error(alert_msg)
            # Here you could add code to trigger an alert (e.g., send an email, notify via HITL interface).

    def clear_logs(self):
        """
        Clear all stored log records.
        """
        self.handler.clear_logs()


# Example usage for testing purposes.
if __name__ == "__main__":
    # Initialize the centralized diagnostics system.
    diag = CentralizedDiagnostics()

    # Get a logger and generate some test messages.
    logger = logging.getLogger("TestDiagnostics")
    logger.error("Test error 1")
    logger.error("Test error 2")
    logger.warning("Test warning 1")
    logger.info("Test informational message")

    # Retrieve and print error logs.
    errors = diag.get_error_logs()
    print("Error logs:")
    for err in errors:
        print(err)

    # Check if error threshold is exceeded (threshold set to 1 for demonstration).
    diag.check_error_threshold(threshold=1)

    # Optionally, clear logs.
    diag.clear_logs()
    print("Logs after clearing:", diag.get_error_logs())
