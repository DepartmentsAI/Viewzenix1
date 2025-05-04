#!/usr/bin/env python
"""
Test runner for Viewzenix integration tests.
Helps verify that our fixes and configurations are working properly.
"""

import unittest
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_runner")

def main():
    """Run the integration tests."""
    logger.info("Starting integration tests")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.path.abspath(os.curdir)}")
    
    # Make sure we can import from the src directory
    sys.path.insert(0, os.path.abspath(os.curdir))
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Try loading tests from the integration directory
    logger.info("Loading integration tests...")
    try:
        integration_tests = loader.discover("src/integration/tests", pattern="test_*.py")
        logger.info(f"Found {integration_tests.countTestCases()} integration tests")
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(integration_tests)
        
        # Report results
        logger.info(f"Tests run: {result.testsRun}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Failures: {len(result.failures)}")
        
        if result.errors:
            logger.error("Test errors:")
            for i, (test, error) in enumerate(result.errors, 1):
                logger.error(f"Error {i}: {test}")
                logger.error(error)
        
        if result.failures:
            logger.error("Test failures:")
            for i, (test, failure) in enumerate(result.failures, 1):
                logger.error(f"Failure {i}: {test}")
                logger.error(failure)
        
        # Return success if all tests passed
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 