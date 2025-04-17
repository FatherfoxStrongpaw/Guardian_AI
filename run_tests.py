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

    # Create test suites
    main_suite = loader.discover('tests', pattern='test_*.py')
    optional_suite = loader.discover('tests_optional', pattern='test_*.py')
    root_suite = loader.discover('.', pattern='test_*.py', top_level_dir='.')

    # Combine all test suites
    all_tests = unittest.TestSuite([main_suite, optional_suite, root_suite])

    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)

    return result

if __name__ == '__main__':
    logger.info("Starting test suite execution...")
    result = run_test_suite()

    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())