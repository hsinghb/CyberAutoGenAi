#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time
import psutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/restart.log')
    ]
)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.processes = {}
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist."""
        directories = ['logs', 'data', 'config']
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Ensured directory exists: {dir_path}")

    def kill_existing_processes(self):
        """Kill any existing project processes."""
        logger.info("Checking for existing processes...")
        
        # Keywords to identify our processes
        process_keywords = [
            "streamlit run",
            "cyberautogenai"
        ]

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = " ".join(proc.cmdline())
                for keyword in process_keywords:
                    if keyword in cmdline:
                        logger.info(f"Killing process {proc.pid}: {cmdline}")
                        os.kill(proc.pid, signal.SIGTERM)
                        time.sleep(1)  # Give process time to terminate
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def start_streamlit(self):
        """Start the Streamlit UI."""
        try:
            entry_script = self.project_root / "run_streamlit.py"
            
            if not entry_script.exists():
                raise FileNotFoundError(f"Entry script not found at {entry_script}")

            log_file = self.project_root / "logs" / "streamlit.log"
            
            # Set up environment variables
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{str(self.project_root)}:{env.get('PYTHONPATH', '')}"
            
            # Add environment variable to indicate we're running in the service manager
            env["RUNNING_IN_SERVICE_MANAGER"] = "1"
            
            cmd = [
                sys.executable,  # Use the current Python interpreter
                "-m", "streamlit", "run",
                str(entry_script),
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--logger.level=debug",  # Changed to debug for more info
                "--logger.messageFormat=%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ]
            
            with open(log_file, 'a') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.project_root),
                    env=env,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
            
            self.processes['streamlit'] = process
            logger.info(f"Started Streamlit UI (PID: {process.pid})")
            
            # Wait a moment to check if process is still running
            time.sleep(2)
            if process.poll() is not None:
                raise RuntimeError("Streamlit process failed to start")
            
        except Exception as e:
            logger.error(f"Failed to start Streamlit: {e}")
            raise

    def check_environment(self):
        """Check if all required environment variables are set."""
        required_vars = [
            "OPENAI_API_KEY",
            "ABUSEIPDB_API_KEY",
            "SHODAN_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("Some features may be limited")
        else:
            logger.info("All required environment variables are set")

    def wait_for_services(self):
        """Wait for all services to be ready."""
        # Wait for Streamlit
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                import requests
                response = requests.get("http://localhost:8501")
                if response.status_code == 200:
                    logger.info("Streamlit UI is ready")
                    break
            except requests.exceptions.ConnectionError:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error("Streamlit UI failed to start")
                    return False
                logger.info(f"Waiting for Streamlit UI... (attempt {retry_count}/{max_retries})")
                time.sleep(2)
        
        return True

    def cleanup(self, signum=None, frame=None):
        """Clean up processes on shutdown."""
        logger.info("Cleaning up processes...")
        
        for service_name, process in self.processes.items():
            try:
                if process.poll() is None:  # Process is still running
                    logger.info(f"Stopping {service_name}...")
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping {service_name}: {e}")
                try:
                    process.kill()  # Force kill if terminate doesn't work
                except Exception:
                    pass

    def run(self):
        """Run the service manager."""
        try:
            # Register signal handlers
            signal.signal(signal.SIGINT, self.cleanup)
            signal.signal(signal.SIGTERM, self.cleanup)

            # Kill any existing processes
            self.kill_existing_processes()

            # Check environment
            self.check_environment()

            # Start services
            logger.info("Starting services...")
            self.start_streamlit()

            # Wait for services to be ready
            if not self.wait_for_services():
                raise RuntimeError("Services failed to start")

            logger.info("All services started successfully")
            logger.info("Access the UI at http://localhost:8501")

            # Keep the script running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error running services: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run() 