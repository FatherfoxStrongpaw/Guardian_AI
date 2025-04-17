import os
import json
import hashlib
import time
import logging

# Configure logging.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("self_diagnostic.log")],
)
logger = logging.getLogger("SelfDiagnostic")

MANIFEST_FILE = "diagnostic_manifest.json"


def compute_file_checksum(file_path):
    """
    Compute the SHA256 checksum of a file.
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
    except Exception as e:
        logger.error("Error computing checksum for %s: %s", file_path, e)
        return None


def load_manifest(manifest_file=MANIFEST_FILE):
    """
    Load the manifest file which contains expected checksums.
    The manifest should be a JSON object mapping file paths to expected checksums.
    Example:
      {
          "baseline/module1.py": "abc123...",
          "baseline/module2.py": "def456..."
      }
    """
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
            logger.info("Manifest loaded successfully.")
            return manifest
        except Exception as e:
            logger.error("Error loading manifest: %s", e)
    else:
        logger.warning(
            "Manifest file %s not found. Starting with an empty manifest.",
            manifest_file,
        )
    return {}


def save_manifest(manifest, manifest_file=MANIFEST_FILE):
    """
    Save the updated manifest to the file.
    """
    try:
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=4)
        logger.info("Manifest saved successfully.")
    except Exception as e:
        logger.error("Error saving manifest: %s", e)


def initialize_manifest():
    """Initialize or update the diagnostic manifest"""
    if not os.path.exists(MANIFEST_FILE):  # Changed from manifest_file to MANIFEST_FILE
        default_manifest = {
            "critical_files": {
                "sandbox_excecuter.py": None,
                "rsi_module.py": None,
                "perpetual_llm.py": None,
                "hitl_interface.py": None,
                "ollama_agent.py": None,
                "sandbox_executor.py": None
            },
            "last_check": None,
            "check_interval": 3600,
            "alert_threshold": 3
        }
        save_manifest(default_manifest)
        logger.info("Initialized new diagnostic manifest")
        return default_manifest
    return load_manifest()


def run_self_diagnostics(critical_files):
    """Run self-diagnostics with enhanced error detection"""
    manifest = initialize_manifest()
    report = {
        "timestamp": time.time(),
        "results": {},
        "alerts": []
    }

    for file_path in critical_files:
        try:
            current_checksum = compute_file_checksum(file_path)
            expected_checksum = manifest["critical_files"].get(file_path)

            result = {
                "expected": expected_checksum,
                "current": current_checksum,
                "match": expected_checksum == current_checksum if expected_checksum else None,
                "status": "ok"
            }

            if result["match"] is False:
                result["status"] = "modified"
                report["alerts"].append(f"File modified: {file_path}")
            elif result["match"] is None:
                result["status"] = "new"
                manifest["critical_files"][file_path] = current_checksum

            report["results"][file_path] = result

        except FileNotFoundError:
            report["results"][file_path] = {
                "status": "missing",
                "error": f"File not found: {file_path}"
            }
            report["alerts"].append(f"Critical file missing: {file_path}")

        except Exception as e:
            report["results"][file_path] = {
                "status": "error",
                "error": str(e)
            }
            report["alerts"].append(f"Error checking {file_path}: {e}")

    manifest["last_check"] = report["timestamp"]
    save_manifest(manifest)

    return report


def print_diagnostic_report(report):
    """
    Pretty-print the diagnostic report.
    """
    print("\n=== Self-Diagnostic Report ===")
    print(f"Report generated at {time.ctime(report['timestamp'])}")
    for file_path, result in report["results"].items():
        status = (
            "MATCH"
            if result["match"]
            else ("MISMATCH" if result["match"] is False else "NEW")
        )
        print(f"File: {file_path}")
        print(f"  Expected Checksum: {result['expected']}")
        print(f"  Current Checksum:  {result['current']}")
        print(f"  Status: {status}")
        print("-" * 40)
    print("=== End of Report ===\n")


# Example usage for testing.
if __name__ == "__main__":
    # List of critical files to monitor.
    critical_files = [
        "perpetual_llm.py",
        "rsi_module.py",
        "sandbox_executor.py",
        "hitl_interface.py",
        "ollama_agent.py",
        "self_diagnostic.py"
    ]
    report = run_self_diagnostics(critical_files)
    print_diagnostic_report(report)
