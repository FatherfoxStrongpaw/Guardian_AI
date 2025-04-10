from enum import Enum
from typing import Callable, Any, Optional
import time
import logging

class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Failing, no attempts
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 fallback: Optional[Callable] = None):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
        self.fallback = fallback

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                return self._handle_open_circuit()

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self._handle_failure(e)
            return self._handle_open_circuit()

    def _handle_failure(self, error: Exception) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
        logging.error(f"Circuit breaker failure: {error}")

    def _handle_open_circuit(self) -> Any:
        if self.fallback:
            return self.fallback()
        raise RuntimeError("Circuit breaker is open")