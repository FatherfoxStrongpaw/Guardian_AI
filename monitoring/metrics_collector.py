from prometheus_client import Counter, Gauge, Histogram, start_http_server
import threading
import time
import psutil
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, config):
        self.config = config
        self.port = config["monitoring"]["metrics_port"]
        
        # Define metrics
        self.directive_counter = Counter(
            'agent_directives_total',
            'Total number of directives processed',
            ['status']
        )
        
        self.memory_usage = Gauge(
            'agent_memory_usage_bytes',
            'Current memory usage of the agent'
        )
        
        self.execution_time = Histogram(
            'agent_execution_time_seconds',
            'Time spent executing directives',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )

        self.health_score = Gauge(
            'agent_health_score',
            'Overall health score of the agent'
        )

        self._start_server()
        self._start_collection()

    def _start_server(self):
        start_http_server(self.port)
        logger.info(f"Metrics server started on port {self.port}")

    def _start_collection(self):
        def collect_metrics():
            while True:
                try:
                    # Update memory usage
                    process = psutil.Process()
                    self.memory_usage.set(process.memory_info().rss)
                    
                    time.sleep(self.config["monitoring"]["health_check_interval"])
                except Exception as e:
                    logger.error(f"Error collecting metrics: {e}")

        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()

    def record_directive(self, status: str):
        """Record a directive execution"""
        self.directive_counter.labels(status=status).inc()

    def record_execution_time(self, duration: float):
        """Record execution time"""
        self.execution_time.observe(duration)

    def update_health_score(self, score: float):
        """Update overall health score"""
        self.health_score.set(score)