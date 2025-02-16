import curses
import random
import logging
from collections import deque
from datetime import datetime
import psutil
from multiprocessing import Process, Manager

from edison.models.CarDateWindow import CarData

# Configure logging
logging.basicConfig(
    filename=f"{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger("MainLogger")

MIN_HEIGHT = 10
MIN_WIDTH = 40
REFRESH_INTERVAL = 50  

class DashboardWindows:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = self.update_dimensions()
        self.create_windows()

    def update_dimensions(self):
        self.height, self.width = self.stdscr.getmaxyx()
        return self.height, self.width

    def create_windows(self):
        """Initialize all application windows based on current terminal size"""
        self.log_win_height = self.height - 6
        self.info_panel_width = self.width // 3

        self.log_win = curses.newwin(self.log_win_height, self.width - 2, 1, 1)
        self.stat_bar = curses.newwin(3, self.width - 2, self.log_win_height + 3, 1)
        self.speed_win = curses.newwin(3, self.info_panel_width - 2, self.log_win_height, 1)
        self.location_win = curses.newwin(3, self.info_panel_width - 2, self.log_win_height, 
                                        self.width - self.info_panel_width + 1)

# Function for updating the stuff

def generate_car_data(location_shared_state, status_shared_state) -> CarData:
    """Generate random vehicle telemetry data"""
    cpu_usage = psutil.cpu_percent(interval=1)

    # Get RAM usage
    memory_info = psutil.virtual_memory()
    ram_usage = memory_info.percent

    return CarData(
        speed=status_shared_state['speed'],
        direction=status_shared_state['direction'],
        location=location_shared_state['location'],
        cpu_usage=cpu_usage,
        ram_usage=ram_usage,
    )

def draw_logs(win, logs):
    """Render scrolling log messages"""
    win.clear()
    win.box()
    max_lines = win.getmaxyx()[0] - 2
    
    for i, log in enumerate(logs):
        if i >= max_lines:
            break
        try:
            win.addstr(i + 1, 2, log[:win.getmaxyx()[1] - 4])
        except curses.error:
            continue

def draw_telemetry(win, title, *lines):
    """Generic function for drawing boxed data panels"""
    win.clear()
    win.box()
    try:
        win.addstr(0, 2, f"[ {title} ]")
        for i, line in enumerate(lines, start=1):
            win.addstr(i, 2, str(line))
    except curses.error:
        pass

def main(stdscr):
    # Initialize curses settings
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(REFRESH_INTERVAL)

    # Initialize dashboard components
    windows = DashboardWindows(stdscr)
    logs = deque(maxlen=windows.log_win_height - 2)

    logging_queue = Manager().dict()
    location_queue = Manager().dict()
    status_queue = Manager().dict()

    while True:
        if stdscr.getch() == curses.KEY_RESIZE:
            windows.update_dimensions()
            if windows.height < MIN_HEIGHT or windows.width < MIN_WIDTH:
                continue  # Skip redraw if below minimum size
            logs = deque(logs, maxlen=windows.log_win_height - 2)
            windows.create_windows()

        # Generate new data
        car_data = generate_car_data(
            logging_queue,
            status_queue
        )

        draw_logs(windows.log_win, logs)
        draw_telemetry(windows.speed_win, "SPEED & DIRECTION", 
                     f"Speed: {car_data.speed} units", 
                     f"Direction: {car_data.direction}")
        draw_telemetry(windows.location_win, "LOCATION",
                     f"Lat: {car_data.location[0]:.5f}",
                     f"Long: {car_data.location[1]:.5f}")
        draw_telemetry(windows.stat_bar, "SYSTEM STATS",
                     f"CPU: {car_data.cpu_usage}% | RAM: {car_data.ram_usage}% | "
                     "Press 'q' to quit")

        # Refresh all windows
        stdscr.refresh()
        windows.log_win.refresh()
        windows.speed_win.refresh()
        windows.location_win.refresh()
        windows.stat_bar.refresh()

        # Check for quit command
        if stdscr.getch() == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)
