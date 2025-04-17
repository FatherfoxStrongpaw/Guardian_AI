import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("DependencyVerifier")

def verify_imports(module_name):
    """Verify that a module can be imported"""
    try:
        module = importlib.import_module(module_name)
        logger.info(f"✓ Successfully imported {module_name}")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import {module_name}: {e}")
        return False

def verify_file_exists(file_path):
    """Verify that a file exists"""
    if os.path.exists(file_path):
        logger.info(f"✓ File exists: {file_path}")
        return True
    else:
        logger.error(f"✗ File not found: {file_path}")
        return False

def main():
    """Main verification function"""
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    # Critical files to check
    critical_files = [
        "perpetual_llm.py",
        "rsi_module.py",
        "sandbox_executor.py",
        "hitl_interface.py",
        "ollama_agent.py",
        "self_diagnostic.py"
    ]
    
    # Verify files exist
    logger.info("Checking file existence...")
    for file in critical_files:
        verify_file_exists(file)
    
    # Verify imports
    logger.info("\nChecking module imports...")
    module_names = [os.path.splitext(file)[0] for file in critical_files]
    for module in module_names:
        verify_imports(module)
    
    # Check for specific dependencies
    logger.info("\nChecking interfile dependencies...")
    
    # Check if perpetual_llm.py imports all required modules
    try:
        import perpetual_llm
        logger.info("Checking perpetual_llm.py dependencies:")
        required_imports = ["rsi_module", "ollama_agent", "memory_manager", "sandbox_executor", "hitl_interface"]
        for imp in required_imports:
            if imp in sys.modules:
                logger.info(f"  ✓ {imp} is imported")
            else:
                logger.warning(f"  ✗ {imp} is not imported")
    except ImportError as e:
        logger.error(f"Could not check perpetual_llm.py dependencies: {e}")

if __name__ == "__main__":
    main()
