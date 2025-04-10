import yaml
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def verify_config_dependencies():
    """Verify configuration dependencies across all modules"""
    try:
        # Load base config
        with open('config/base_config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        # Required configuration keys for each module
        required_configs = {
            'rsi_module': [
                'system.debug',
                'security.sandbox.enabled',
                'llm.provider'
            ],
            'perpetual_agent': [
                'llm.model',
                'llm.temperature',
                'memory.type'
            ],
            'sandbox_executor': [
                'security.sandbox.timeout',
                'security.sandbox.max_memory'
            ],
            'memory_manager': [
                'memory.type',
                'memory.path'
            ]
        }

        # Verify each module's config requirements
        for module, keys in required_configs.items():
            logger.info(f"\nChecking {module} configuration requirements:")
            for key in keys:
                parts = key.split('.')
                current = config
                try:
                    for part in parts:
                        current = current[part]
                    logger.info(f"✓ Found: {key}")
                except (KeyError, TypeError):
                    logger.error(f"✗ Missing: {key}")

    except Exception as e:
        logger.error(f"Configuration verification failed: {e}")

if __name__ == "__main__":
    logger.info("Starting configuration verification...")
    verify_config_dependencies()