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


def run_self_diagnostics(critical_files):
    """
    Run self-diagnostics by checking the checksums of critical files.

    Parameters:
      - critical_files: a list of file paths to monitor.

    Returns:
      A diagnostic report (dictionary) indicating:
        - Each file's expected checksum,
        - Its current checksum,
        - Whether it matches.
    """
    manifest = load_manifest()
    report = {"timestamp": time.time(), "results": {}}
    for file_path in critical_files:
        expected_checksum = manifest.get(file_path)
        current_checksum = compute_file_checksum(file_path)
        match = (expected_checksum == current_checksum) if expected_checksum else None

        report["results"][file_path] = {
            "expected": expected_checksum,
            "current": current_checksum,
            "match": match,
        }
        if match is False:
            logger.error(
                "Checksum mismatch for %s! Expected %s, got %s",
                file_path,
                expected_checksum,
                current_checksum,
            )
        elif match is None:
            logger.info(
                "No baseline checksum for %s. Recording current checksum.", file_path
            )
            manifest[file_path] = current_checksum
        else:
            logger.info("Checksum verified for %s.", file_path)

    # Save manifest in case new entries were added.
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
    # List of critical files to monitor. Adjust these paths as needed.
    critical_files = ["baseline/module1.py", "baseline/module2.py", "config.json"]
    report = run_self_diagnostics(critical_files)
    print_diagnostic_report(report)
