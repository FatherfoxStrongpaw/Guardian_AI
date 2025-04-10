import os
import json
import time
import hashlib
import logging
import tempfile
import shutil
from typing import Any, Optional
import sqlite3
from datetime import datetime, timedelta

# Configure logging to output to both console and a file.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("memory_manager.log")],
)

logger = logging.getLogger("MemoryManager")


class MemoryManager:
    """
    A robust persistent memory manager that stores data in a JSON file using atomic writes,
    creates versioned backups, calculates checksums for data integrity, and logs all operations.
    """

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_path)
            self._initialize_db()
            logger.info("Memory Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Memory Manager: {e}")

    def cleanup(self):
        """Cleanup database connections"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Memory Manager connections closed")

    def _compute_checksum(self, data_bytes):
        """
        Compute a SHA256 checksum of the given data bytes.
        :param data_bytes: Data in bytes.
        :return: Hexadecimal checksum string.
        """
        return hashlib.sha256(data_bytes).hexdigest()

    def atomic_write(self, filename, data_str):
        """
        Write data to a file atomically by writing to a temporary file first, then moving it.
        :param filename: Target file path.
        :param data_str: Data to write (a JSON string).
        """
        dir_name = os.path.dirname(filename) or "."
        # Create a temporary file in the target directory.
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tf:
            temp_name = tf.name
            tf.write(data_str)
            tf.flush()
            os.fsync(tf.fileno())
        # Atomically replace the target file.
        shutil.move(temp_name, filename)
        logger.info("Atomic write successful: %s", filename)

    def load_memory(self):
        """
        Load memory records from the JSON file if it exists; otherwise, initialize empty memory.
        Verifies data integrity using checksum if desired.
        """
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "rb") as f:
                    raw_data = f.read()
                    checksum = self._compute_checksum(raw_data)
                    data_str = raw_data.decode("utf-8")
                    data = json.loads(data_str)
                self.memory = data
                logger.info(
                    "Memory loaded: %d records. Checksum: %s",
                    len(self.memory),
                    checksum,
                )
            except Exception as e:
                logger.error("Failed to load memory: %s", e)
                self.memory = []
        else:
            self.memory = []
            logger.info("Memory file not found. Starting with empty memory.")

    def save_memory(self):
        """
        Save memory data atomically to a JSON file, create a versioned backup, and log the operation.
        """
        try:
            # Serialize memory data to a JSON string.
            data_str = json.dumps(self.memory, indent=4)
            data_bytes = data_str.encode("utf-8")
            checksum = self._compute_checksum(data_bytes)
            logger.info(
                "Saving memory: %d records. Computed checksum: %s",
                len(self.memory),
                checksum,
            )

            # Write data atomically.
            self.atomic_write(self.memory_file, data_str)

            logger.info("Memory saved successfully to %s.", self.memory_file)

            # Create a versioned backup.
            backup_filename = os.path.join(
                self.backup_dir, f"memory_backup_{int(time.time())}.json"
            )
            shutil.copy2(self.memory_file, backup_filename)
            logger.info("Backup created: %s", backup_filename)
        except Exception as e:
            logger.error("Failed to save memory: %s", e)

    def add_record(self, record):
        """
        Add a new record to memory, log the operation, and then save the updated memory.
        :param record: A dictionary representing the record to add.
        """
        entry = {"timestamp": time.time(), "record": record}
        self.memory.append(entry)
        logger.info("Record added: %s", record)
        self.save_memory()

    def get_records(self, filter_func=None):
        """
        Retrieve memory records, optionally filtering by a provided function.
        :param filter_func: A function to filter records.
        :return: List of memory records.
        """
        if filter_func:
            return list(filter(filter_func, self.memory))
        return self.memory

    def rollback_last(self):
        """
        Remove the most recent record, log the rollback, and save the updated memory.
        :return: The removed record or None if no records exist.
        """
        if self.memory:
            removed = self.memory.pop()
            logger.info("Rolled back record: %s", removed)
            self.save_memory()
            return removed
        logger.warning("No records available for rollback.")
        return None


# Test hook for standalone execution.
if __name__ == "__main__":
    mm = MemoryManager()
    mm.add_record({"action": "initialize", "detail": "System boot"})
    records = mm.get_records()
    logger.info("Current memory: %s", records)
