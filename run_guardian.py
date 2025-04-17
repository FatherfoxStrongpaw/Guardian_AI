#!/usr/bin/env python3
import os
import sys
import logging
import subprocess
import time
import signal
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("guardian.log")
    ]
)
logger = logging.getLogger("GuardianRunner")

def run_verification():
    """Run verification scripts"""
    logger.info("Running verification...")
    
    # Run self-diagnostics
    logger.info("Running self-diagnostics...")
    try:
        result = subprocess.run(
            ["python", "self_diagnostic.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Self-diagnostics completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Self-diagnostics failed: {e.stderr}")
        return False
    
    # Run final verification
    logger.info("Running final verification...")
    try:
        result = subprocess.run(
            ["python", "final_verification.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Final verification completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Final verification failed: {e.stderr}")
        return False
    
    return True

def run_guardian(debug=False):
    """Run the Guardian AI system"""
    logger.info("Starting Guardian AI...")
    
    cmd = ["python", "perpetual_llm.py"]
    if debug:
        # Run in foreground with output
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Guardian AI exited with error: {e}")
            return False
        except KeyboardInterrupt:
            logger.info("Guardian AI stopped by user")
    else:
        # Run in background
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Guardian AI started with PID {process.pid}")
            
            # Wait a bit to check for immediate failures
            time.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"Guardian AI failed to start: {stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to start Guardian AI: {e}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run Guardian AI system")
    parser.add_argument("--skip-verification", action="store_true", help="Skip verification steps")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode (foreground)")
    args = parser.parse_args()
    
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())
    
    # Run verification unless skipped
    if not args.skip_verification:
        if not run_verification():
            logger.error("Verification failed, aborting")
            return 1
    
    # Run Guardian AI
    success = run_guardian(debug=args.debug)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
