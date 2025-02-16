# workers.py
import curses
import time
from edison._lib.Dashboard import DashboardManager, DataHandler


def run_dashboard(logs_shared_state, location_state, status_state):
    """Wrapper function to run curses dashboard in a subprocess"""
    curses.wrapper(main_dashboard, logs_shared_state, location_state, status_state)

def main_dashboard(stdscr, logs_shared_state, location_state, status_state):
    """
    Main dashboard logic running in a curses environment.
    Receives shared state through parameters.
    """
    stdscr.nodelay(True)
    
    # Initialize dashboard components with shared state
    dashboard = DashboardManager(stdscr, logs_shared_state)
    data_handler = DataHandler(location_state, status_state)

    # Initial log messages
    logs_shared_state.put("Dashboard started, initiazling and checking conditions")

    try:
        while True:
            key = stdscr.getch()

            if key == curses.KEY_RESIZE:
                dashboard.handle_resize()

            if key == ord('q'):
                break

            dashboard.update_logs()
            car_data = data_handler.generate_car_data()

            # Update dashboard panels
            dashboard.draw_logs()
            dashboard.draw_telemetry_panel(
                dashboard.windows.speed_win, "SPEED & DIRECTION",
                f"Speed: {car_data.speed} units",
                f"Direction: {car_data.direction}"
            )
            dashboard.draw_telemetry_panel(
                dashboard.windows.location_win, "LOCATION",
                f"Lat: {car_data.location[0]:.5f}",
                f"Long: {car_data.location[1]:.5f}"
            )
            dashboard.draw_telemetry_panel(
                dashboard.windows.stat_bar, "SYSTEM STATS",
                f"CPU: {car_data.cpu_usage}% | RAM: {car_data.ram_usage}%",
                "Press 'q' to quit"
            )

            dashboard.refresh_all()
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
