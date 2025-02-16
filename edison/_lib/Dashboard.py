import curses
import psutil
from typing import Deque, Tuple
from multiprocessing import Manager
from collections import deque

from edison.models.CarDateWindow import CarData  # Ensure this import is correct

# TODO: add to .env
MIN_HEIGHT = 10
MIN_WIDTH = 40
REFRESH_INTERVAL = 50


class DashboardWindows:
    """Manage terminal windows and their dimensions"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height: int
        self.width: int
        self.log_win: curses.window
        self.stat_bar: curses.window
        self.speed_win: curses.window
        self.location_win: curses.window
        self.update_dimensions()
        self.create_windows()

    def update_dimensions(self) -> Tuple[int, int]:
        """Update terminal dimensions and return (height, width)"""
        self.height, self.width = self.stdscr.getmaxyx()
        return self.height, self.width

    def create_windows(self) -> None:
        """(Re)create all windows based on current terminal size"""
        self.log_win_height = self.height - 6
        self.info_panel_width = self.width // 3

        # Main log window
        self.log_win = curses.newwin(self.log_win_height, self.width - 2, 1, 1)
        
        # Bottom status bar
        self.stat_bar = curses.newwin(3, self.width - 2, self.log_win_height + 3, 1)
        
        # Side panels (for speed/direction and location)
        self.speed_win = curses.newwin(3, self.info_panel_width - 2, self.log_win_height, 1)
        self.location_win = curses.newwin(
            3, self.info_panel_width - 2, self.log_win_height,
            self.width - self.info_panel_width + 1
        )


class DashboardManager:
    """Handle dashboard rendering and state management"""
    def __init__(self, stdscr, logs_shared_state):
        self.stdscr = stdscr
        self.logs_shared_state = logs_shared_state  # Shared log queue
        self.windows = DashboardWindows(stdscr)
        self.logs: Deque[str] = deque(maxlen=self.windows.log_win_height - 2)
        
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(REFRESH_INTERVAL)

    def update_logs(self) -> None:
        """Continuously fetch new logs from the shared queue"""
        while not self.logs_shared_state.empty():
            log_entry = self.logs_shared_state.get()
            self.logs.append("[+] " + log_entry)

    def handle_resize(self) -> None:
        """Handle terminal resize events"""
        self.windows.update_dimensions()
        if self.windows.height >= MIN_HEIGHT and self.windows.width >= MIN_WIDTH:
            self.logs = deque(self.logs, maxlen=self.windows.log_win_height - 2)
            self.windows.create_windows()

    def draw_logs(self) -> None:
        """Render scrolling log messages"""
        self.windows.log_win.clear()
        self.windows.log_win.box()
        
        for i, log in enumerate(self.logs):
            if i >= self.windows.log_win.getmaxyx()[0] - 2:
                break
            self.windows.log_win.addstr(i + 1, 2, log[:self.windows.log_win.getmaxyx()[1] - 4])

    def draw_telemetry_panel(self, win: curses.window, title: str, line1: str, line2: str) -> None:
        """Draw a panel with a border, title, and two lines of telemetry data"""
        win.clear()
        win.box()
        max_y, max_x = win.getmaxyx()
        try:
            # Center the title in the top border
            title_str = f' {title} '
            start_x = max((max_x - len(title_str)) // 2, 0)
            win.addstr(0, start_x, title_str)
        except curses.error:
            pass  # In case window is too small
        try:
            # Draw telemetry data lines (ensure text fits within window width)
            win.addstr(1, 2, line1[:max_x-4])
            win.addstr(2, 2, line2[:max_x-4])
        except curses.error:
            pass

    def refresh_all(self) -> None:
        """Refresh all windows"""
        self.stdscr.refresh()
        self.windows.log_win.refresh()
        self.windows.speed_win.refresh()
        self.windows.location_win.refresh()
        self.windows.stat_bar.refresh()


class DataHandler:
    """Manage shared state and data generation"""
    def __init__(self, location_state, status_state):
        self.manager = Manager()
        self.location_state = location_state
        self.status_state = status_state
        self._init_shared_state()

    def _init_shared_state(self) -> None:
        """Initialize shared state with default values"""
        self.location_state['location'] = (0.0, 0.0)
        self.status_state['speed'] = 0
        self.status_state['direction'] = 'N'

    def generate_car_data(self) -> CarData:
        """Generate current vehicle telemetry data"""
        return CarData(
            speed=self.status_state['speed'],
            direction=self.status_state['direction'],
            location=self.location_state['location'],
            cpu_usage=psutil.cpu_percent(interval=1),
            ram_usage=psutil.virtual_memory().percent,
        )
