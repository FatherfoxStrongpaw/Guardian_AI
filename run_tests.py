import unittest
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('TestRunner')

def run_test_suite():
    """Run all tests and return the result"""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == '__main__':
    logger.info("Starting test suite execution...")
    result = run_test_suite()
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())