# __main__.py
import logging
from datetime import datetime
from multiprocessing import Manager, Process, freeze_support
from edison._lib.workers import run_dashboard  # Import from the new module

# Configure logging
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MainLogger")

if __name__ == "__main__":
    freeze_support()  # Optional but recommended on Windows
    with Manager() as manager:
        logs_shared_state = manager.Queue()
        location_state = manager.dict()
        status_state = manager.dict()

        # Create and start processes
        dashboard_process = Process(
            target=run_dashboard,
            args=(logs_shared_state, location_state, status_state)
        )
        
        dashboard_process.start()

        # Wait for dashboard to complete
        dashboard_process.join()
