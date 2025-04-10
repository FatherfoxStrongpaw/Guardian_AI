import logging
import shutil
import os
from typing import Dict, Optional
import json
import time

logger = logging.getLogger(__name__)

class SystemRecovery:
    def __init__(self, config: Dict):
        self.config = config
        self.backup_dir = "backups"
        self.recovery_log = "recovery/recovery_log.json"
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.recovery_log), exist_ok=True)

    def create_backup(self, trigger: str) -> str:
        """Create backup of critical files"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
        os.makedirs(backup_path)

        with open('diagnostic_manifest.json', 'r') as f:
            manifest = json.load(f)

        for file_path in manifest['critical_files']:
            if os.path.exists(file_path):
                dest_path = os.path.join(backup_path, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)

        # Log backup creation
        self.log_recovery_event({
            'type': 'backup',
            'trigger': trigger,
            'timestamp': timestamp,
            'path': backup_path
        })

        return backup_path

    def restore_from_backup(self, backup_path: Optional[str] = None) -> bool:
        """Restore system from backup"""
        if not backup_path:
            # Get latest backup
            backups = [d for d in os.listdir(self.backup_dir) 
                      if os.path.isdir(os.path.join(self.backup_dir, d))]
            if not backups:
                logger.error("No backups found")
                return False
            backup_path = os.path.join(self.backup_dir, sorted(backups)[-1])

        try:
            # Restore files
            for file_name in os.listdir(backup_path):
                source = os.path.join(backup_path, file_name)
                destination = file_name  # Restore to original location
                shutil.copy2(source, destination)

            self.log_recovery_event({
                'type': 'restore',
                'timestamp': time.strftime("%Y%m%d_%H%M%S"),
                'backup_used': backup_path
            })
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def log_recovery_event(self, event: Dict):
        """Log recovery events"""
        try:
            if os.path.exists(self.recovery_log):
                with open(self.recovery_log, 'r') as f:
                    log = json.load(f)
            else:
                log = []

            log.append(event)

            with open(self.recovery_log, 'w') as f:
                json.dump(log, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log recovery event: {e}")

    def cleanup_old_backups(self, max_age_days: int = 7):
        """Remove backups older than specified days"""
        current_time = time.time()
        for backup in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, backup)
            if os.path.isdir(backup_path):
                creation_time = os.path.getctime(backup_path)
                if (current_time - creation_time) > (max_age_days * 86400):
                    shutil.rmtree(backup_path)
                    logger.info(f"Removed old backup: {backup}")