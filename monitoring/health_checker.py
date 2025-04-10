import psutil
import time
import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self, config: Dict):
        self.config = config
        self.critical_thresholds = {
            'cpu_percent': 90,
            'memory_percent': 85,
            'disk_percent': 90
        }
        self.warning_count = 0
        self.max_warnings = config.get('alert_threshold', 3)

    def check_system_resources(self) -> Dict:
        """Check CPU, memory, and disk usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }

    def check_critical_files(self) -> List[Dict]:
        """Verify integrity of critical files"""
        issues = []
        with open('diagnostic_manifest.json', 'r') as f:
            manifest = json.load(f)
            
        for file_path in manifest['critical_files']:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if not content:
                        issues.append({
                            'file': file_path,
                            'issue': 'Empty file'
                        })
            except Exception as e:
                issues.append({
                    'file': file_path,
                    'issue': str(e)
                })
        
        return issues

    def check_database_connection(self) -> bool:
        """Verify database connectivity"""
        try:
            # Using the existing DB connection from memory_manager
            from memory_manager import MemoryManager
            mm = MemoryManager(self.config)
            mm.retrieve('health_check')
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    def run_health_check(self) -> Dict:
        """Run comprehensive health check"""
        resources = self.check_system_resources()
        critical_files = self.check_critical_files()
        db_status = self.check_database_connection()

        status = 'healthy'
        alerts = []

        # Check resource thresholds
        for resource, value in resources.items():
            if value > self.critical_thresholds[resource]:
                alerts.append(f"Critical: {resource} at {value}%")
                status = 'critical'

        # Check file issues
        if critical_files:
            alerts.append(f"Critical files have issues: {len(critical_files)} problems found")
            status = 'critical'

        # Check database
        if not db_status:
            alerts.append("Database connection failed")
            status = 'critical'

        if status == 'critical':
            self.warning_count += 1
        else:
            self.warning_count = 0

        needs_restart = self.warning_count >= self.max_warnings

        return {
            'timestamp': time.time(),
            'status': status,
            'resources': resources,
            'file_issues': critical_files,
            'database_status': db_status,
            'alerts': alerts,
            'needs_restart': needs_restart
        }