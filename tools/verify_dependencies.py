import sys
import importlib
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def verify_module_dependencies(module_path):
    """Verify all dependencies for a given module"""
    try:
        # Add parent directory to path for imports
        parent = str(Path(module_path).parent.parent)
        sys.path.insert(0, parent)
        
        # Import the module
        module_name = Path(module_path).stem
        module = importlib.import_module(module_name)
        
        # Get all imported modules
        imports = set()
        for attr_name in dir(module):
            try:
                attr = getattr(module, attr_name)
                if hasattr(attr, '__module__') and attr.__module__:
                    imports.add(attr.__module__)
            except Exception as e:
                logger.warning(f"Could not check attribute {attr_name}: {e}")
        
        logger.info(f"\nModule: {module_name}")
        logger.info("Dependencies:")
        for imp in sorted(imports):
            try:
                importlib.import_module(imp)
                logger.info(f"✓ {imp}")
            except ImportError as e:
                logger.error(f"✗ {imp}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to verify {module_path}: {e}")

if __name__ == "__main__":
    critical_files = [
        "rsi_module.py",
        "perpetual_agent.py",
        "hitl_interface.py",
        "sandbox_executor.py",
        "memory_manager.py",
        "consolidated_code_analysis.py"
    ]
    
    logger.info("Starting dependency verification...")
    for file in critical_files:
        verify_module_dependencies(file)