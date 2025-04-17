import os
import json
import time
import hashlib
import logging
import tempfile
import shutil
import sqlite3
from resilience.circuit_breaker import CircuitBreaker

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
        self.memory_file = "data/memory.json"  # For backward compatibility
        self.backup_dir = "backups"  # For backward compatibility

        # Create necessary directories
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        # Initialize memory
        self.memory = []

        # Initialize circuit breaker for database operations
        self.db_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            fallback=self._db_operation_fallback
        )

        # Initialize database connection
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_path)
            self._initialize_db()
            logger.info("Memory Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Memory Manager: {e}")

    def _initialize_db(self):
        """Initialize the database tables"""
        cursor = self.conn.cursor()

        # Create memory table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            type TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            expires_at INTEGER
        )
        """)

        # Create file hash table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_hashes (
            file_path TEXT PRIMARY KEY,
            hash_value TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """)

        # Create memory records table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            record TEXT NOT NULL
        )
        """)

        # Create file versions table for versioning
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            hash_value TEXT NOT NULL,
            content BLOB,
            timestamp INTEGER NOT NULL,
            change_description TEXT
        )
        """)

        # Create file monitoring table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_monitoring (
            file_path TEXT PRIMARY KEY,
            last_checked INTEGER NOT NULL,
            status TEXT NOT NULL,
            is_critical INTEGER NOT NULL DEFAULT 0
        )
        """)

        # Create changelog table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            file_path TEXT,
            action TEXT NOT NULL,
            details TEXT,
            user TEXT
        )
        """)

        self.conn.commit()
        logger.info("Database tables initialized")

    def get_hash(self, file_path: str) -> str:
        """Get the stored hash for a file"""
        if not self.conn:
            logger.warning("Database connection not available")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT hash_value FROM file_hashes WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting hash for {file_path}: {e}")
            return None

    def store_hash(self, file_path: str, hash_value: str):
        """Store a hash for a file"""
        if not self.conn:
            logger.warning("Database connection not available")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO file_hashes (file_path, hash_value, timestamp) VALUES (?, ?, ?)",
                (file_path, hash_value, int(time.time()))
            )
            self.conn.commit()
            logger.info(f"Stored hash for {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error storing hash for {file_path}: {e}")
            return False

    def get_status(self):
        """Get the status of the memory manager"""
        if not self.conn:
            return "Database connection not available"

        try:
            cursor = self.conn.cursor()

            # Count file hashes
            cursor.execute("SELECT COUNT(*) FROM file_hashes")
            hash_count = cursor.fetchone()[0]

            # Count memory records
            cursor.execute("SELECT COUNT(*) FROM memory_records")
            record_count = cursor.fetchone()[0]

            return f"OK (Hashes: {hash_count}, Records: {record_count})"
        except Exception as e:
            logger.error(f"Error getting memory status: {e}")
            return f"Error: {str(e)}"

    def _db_operation_fallback(self, operation_type="unknown"):
        """Fallback for database operations when circuit breaker is open"""
        logger.warning("Circuit breaker is open for database operations, using fallback")

        if operation_type == 'store':
            return False
        elif operation_type == 'retrieve':
            return None
        elif operation_type == 'log_execution':
            return False
        else:
            return None

    def _get_connection(self):
        """Get a database connection with context manager support"""
        from contextlib import contextmanager

        @contextmanager
        def connection():
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                yield conn
                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                if conn:
                    conn.close()

        return connection()

    def _execute_store(self, key, serialized, type_hint, timestamp, expires_at):
        """Execute the actual store operation"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory (key, value, type, timestamp, expires_at) VALUES (?, ?, ?, ?, ?)",
                (key, serialized, type_hint, timestamp, expires_at)
            )
            return True

    def _execute_retrieve(self, key):
        """Execute the actual retrieve operation"""
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT value, expires_at FROM memory WHERE key = ?",
                (key,)
            ).fetchone()

            if not result:
                return None

            value, expires_at = result
            if expires_at and time.time() > expires_at:
                conn.execute("DELETE FROM memory WHERE key = ?", (key,))
                return None

            return value

    def store(self, key, value, type_hint="general", ttl=None):
        """Store a value with optional TTL using circuit breaker protection"""
        try:
            serialized = json.dumps(value)
            timestamp = time.time()
            expires_at = timestamp + ttl if ttl else None

            success = self.db_circuit_breaker.execute(
                self._execute_store,
                key, serialized, type_hint, timestamp, expires_at
            )

            if success:
                logger.debug(f"Stored key: {key} of type: {type_hint}")
            return success
        except Exception as e:
            logger.error(f"Error storing key {key}: {e}")
            return False

    def retrieve(self, key):
        """Retrieve a value, respecting TTL, with circuit breaker protection"""
        try:
            result = self.db_circuit_breaker.execute(
                self._execute_retrieve,
                key
            )

            if result is None:
                return None

            return json.loads(result)
        except Exception as e:
            logger.error(f"Error retrieving key {key}: {e}")
            return None

    def cleanup(self):
        """Cleanup database connections"""
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
                self.conn = None
                logger.info("Memory Manager connections closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")

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

    def store_file_version(self, file_path: str, content: bytes, change_description: str = None):
        """Store a version of a file"""
        if not self.conn:
            logger.warning("Database connection not available")
            return False

        try:
            # Calculate hash
            hash_value = hashlib.sha256(content).hexdigest()

            # Store in file_versions table
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO file_versions (file_path, hash_value, content, timestamp, change_description) VALUES (?, ?, ?, ?, ?)",
                (file_path, hash_value, content, int(time.time()), change_description)
            )

            # Update file_hashes table
            self.store_hash(file_path, hash_value)

            # Add to changelog
            self.add_changelog_entry(file_path, "version_stored", change_description)

            self.conn.commit()
            logger.info(f"Stored version of {file_path} with hash {hash_value[:8]}")
            return True
        except Exception as e:
            logger.error(f"Error storing file version for {file_path}: {e}")
            return False

    def get_file_versions(self, file_path: str, limit: int = 10):
        """Get version history for a file"""
        if not self.conn:
            logger.warning("Database connection not available")
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, hash_value, timestamp, change_description FROM file_versions WHERE file_path = ? ORDER BY timestamp DESC LIMIT ?",
                (file_path, limit)
            )
            versions = []
            for row in cursor.fetchall():
                versions.append({
                    "id": row[0],
                    "hash": row[1],
                    "timestamp": row[2],
                    "description": row[3],
                    "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[2]))
                })
            return versions
        except Exception as e:
            logger.error(f"Error getting file versions for {file_path}: {e}")
            return []

    def restore_file_version(self, version_id: int):
        """Restore a specific version of a file"""
        if not self.conn:
            logger.warning("Database connection not available")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT file_path, content, hash_value FROM file_versions WHERE id = ?",
                (version_id,)
            )
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Version {version_id} not found")
                return None

            file_path, content, hash_value = result

            # Add to changelog
            self.add_changelog_entry(file_path, "version_restored", f"Restored to version {version_id}")

            return {
                "file_path": file_path,
                "content": content,
                "hash": hash_value
            }
        except Exception as e:
            logger.error(f"Error restoring file version {version_id}: {e}")
            return None

    def register_monitored_file(self, file_path: str, is_critical: bool = False):
        """Register a file for monitoring"""
        if not self.conn:
            logger.warning("Database connection not available")
            return False

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"File {file_path} does not exist")
                return False

            # Calculate initial hash
            with open(file_path, 'rb') as f:
                content = f.read()
                hash_value = hashlib.sha256(content).hexdigest()

            # Store initial version
            self.store_file_version(file_path, content, "Initial version")

            # Register for monitoring
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO file_monitoring (file_path, last_checked, status, is_critical) VALUES (?, ?, ?, ?)",
                (file_path, int(time.time()), "ok", 1 if is_critical else 0)
            )

            self.conn.commit()
            logger.info(f"Registered {file_path} for monitoring (critical: {is_critical})")
            return True
        except Exception as e:
            logger.error(f"Error registering file {file_path} for monitoring: {e}")
            return False

    def check_monitored_files(self):
        """Check all monitored files for changes"""
        if not self.conn:
            logger.warning("Database connection not available")
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_path, is_critical FROM file_monitoring")
            monitored_files = cursor.fetchall()

            results = []
            for file_path, is_critical in monitored_files:
                result = self.check_file_integrity(file_path, is_critical)
                results.append(result)

            return results
        except Exception as e:
            logger.error(f"Error checking monitored files: {e}")
            return []

    def check_file_integrity(self, file_path: str, is_critical: bool = False):
        """Check if a file has been modified"""
        try:
            # Get stored hash
            stored_hash = self.get_hash(file_path)
            if not stored_hash:
                return {"file_path": file_path, "status": "unknown", "error": "No stored hash"}

            # Check if file exists
            if not os.path.exists(file_path):
                self.add_changelog_entry(file_path, "integrity_check", "File missing")
                return {"file_path": file_path, "status": "missing", "is_critical": is_critical}

            # Calculate current hash
            with open(file_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()

            # Update last checked timestamp
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE file_monitoring SET last_checked = ? WHERE file_path = ?",
                (int(time.time()), file_path)
            )

            # Compare hashes
            if current_hash != stored_hash:
                status = "modified"
                self.add_changelog_entry(file_path, "integrity_check", f"File modified (hash: {current_hash[:8]})")

                # Update status in monitoring table
                cursor.execute(
                    "UPDATE file_monitoring SET status = ? WHERE file_path = ?",
                    (status, file_path)
                )

                self.conn.commit()
                return {"file_path": file_path, "status": status, "is_critical": is_critical}
            else:
                # Update status in monitoring table
                cursor.execute(
                    "UPDATE file_monitoring SET status = ? WHERE file_path = ?",
                    ("ok", file_path)
                )

                self.conn.commit()
                return {"file_path": file_path, "status": "ok", "is_critical": is_critical}
        except Exception as e:
            logger.error(f"Error checking integrity of {file_path}: {e}")
            return {"file_path": file_path, "status": "error", "error": str(e), "is_critical": is_critical}

    def add_changelog_entry(self, file_path: str = None, action: str = None, details: str = None, user: str = None):
        """Add an entry to the changelog"""
        if not self.conn:
            logger.warning("Database connection not available")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO changelog (timestamp, file_path, action, details, user) VALUES (?, ?, ?, ?, ?)",
                (int(time.time()), file_path, action, details, user)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding changelog entry: {e}")
            return False

    def get_changelog(self, limit: int = 100, file_path: str = None):
        """Get recent changelog entries"""
        if not self.conn:
            logger.warning("Database connection not available")
            return []

        try:
            cursor = self.conn.cursor()
            if file_path:
                cursor.execute(
                    "SELECT id, timestamp, file_path, action, details, user FROM changelog WHERE file_path = ? ORDER BY timestamp DESC LIMIT ?",
                    (file_path, limit)
                )
            else:
                cursor.execute(
                    "SELECT id, timestamp, file_path, action, details, user FROM changelog ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )

            entries = []
            for row in cursor.fetchall():
                entries.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[1])),
                    "file_path": row[2],
                    "action": row[3],
                    "details": row[4],
                    "user": row[5]
                })
            return entries
        except Exception as e:
            logger.error(f"Error getting changelog: {e}")
            return []


# Test hook for standalone execution.
if __name__ == "__main__":
    mm = MemoryManager()
    mm.add_record({"action": "initialize", "detail": "System boot"})
    records = mm.get_records()
    logger.info("Current memory: %s", records)
