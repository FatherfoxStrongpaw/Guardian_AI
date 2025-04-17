import os
import sys
import importlib
import logging
import hashlib
import json
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("FinalVerification")

def verify_file_integrity(manifest_file="diagnostic_manifest.json") -> Tuple[bool, Dict]:
    """Verify the integrity of critical files"""
    try:
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        critical_files = manifest.get("critical_files", {})
        results = {}
        all_pass = True
        
        for file_path, expected_hash in critical_files.items():
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                results[file_path] = {"status": "missing", "expected": expected_hash}
                if expected_hash is not None:  # Only fail if we expected this file
                    all_pass = False
                continue
            
            # Compute current hash
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for block in iter(lambda: f.read(4096), b""):
                    sha256.update(block)
            current_hash = sha256.hexdigest()
            
            # Check if hash matches
            if expected_hash is None:
                results[file_path] = {"status": "new", "current": current_hash}
            elif current_hash == expected_hash:
                results[file_path] = {"status": "match", "current": current_hash, "expected": expected_hash}
            else:
                results[file_path] = {"status": "mismatch", "current": current_hash, "expected": expected_hash}
                all_pass = False
        
        return all_pass, results
    
    except Exception as e:
        logger.error(f"Error verifying file integrity: {e}")
        return False, {}

def verify_imports() -> Tuple[bool, List[str]]:
    """Verify that all required modules can be imported"""
    required_modules = [
        'perpetual_llm',
        'rsi_module',
        'sandbox_executor',
        'hitl_interface',
        'ollama_agent',
        'memory_manager'
    ]
    
    errors = []
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            errors.append(f"Failed to import {module_name}: {e}")
    
    return len(errors) == 0, errors

def verify_config() -> Tuple[bool, Dict]:
    """Verify the configuration files"""
    config_files = [
        "config/base_config.yaml",
        "config.json"
    ]
    
    results = {}
    all_pass = True
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            logger.warning(f"Config file not found: {config_file}")
            results[config_file] = {"status": "missing"}
            all_pass = False
            continue
        
        results[config_file] = {"status": "exists"}
    
    return all_pass, results

def main():
    """Main verification function"""
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    logger.info("Starting final verification...")
    
    # Verify file integrity
    logger.info("\nVerifying file integrity...")
    integrity_pass, integrity_results = verify_file_integrity()
    
    if integrity_pass:
        logger.info("✓ All files passed integrity check")
    else:
        logger.warning("✗ Some files failed integrity check")
        
    for file_path, result in integrity_results.items():
        status_symbol = "✓" if result["status"] in ["match", "new"] else "✗"
        logger.info(f"{status_symbol} {file_path}: {result['status']}")
    
    # Verify imports
    logger.info("\nVerifying module imports...")
    imports_pass, import_errors = verify_imports()
    
    if imports_pass:
        logger.info("✓ All modules imported successfully")
    else:
        logger.warning("✗ Some modules failed to import")
        for error in import_errors:
            logger.warning(f"  - {error}")
    
    # Verify configuration
    logger.info("\nVerifying configuration files...")
    config_pass, config_results = verify_config()
    
    if config_pass:
        logger.info("✓ All configuration files exist")
    else:
        logger.warning("✗ Some configuration files are missing")
        for file_path, result in config_results.items():
            status_symbol = "✓" if result["status"] == "exists" else "✗"
            logger.info(f"{status_symbol} {file_path}: {result['status']}")
    
    # Final result
    if integrity_pass and imports_pass and config_pass:
        logger.info("\n✓ Final verification PASSED")
        return 0
    else:
        logger.warning("\n✗ Final verification FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
