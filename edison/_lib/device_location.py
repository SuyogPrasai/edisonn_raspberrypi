import subprocess
import re
from typing import Optional, Tuple

class DeviceLocationReader:
    """
    A class to read and parse device location and direction data from ADB logcat output.

    Attributes:
        location_pattern (re.Pattern): A compiled regex pattern to extract location and direction data.
        location (Optional[Tuple[float, float]]): The current device location as (latitude, longitude).
        direction (Optional[int]): The current device direction in degrees.
        general_direction (Optional[str]): The general direction description (e.g., "North").
    """

    def __init__(self) -> None:
        """
        Initializes the DeviceLocationReader with a regex pattern and default attribute values.
        """
        # Regex pattern to extract location and direction from logcat output
        self.location_pattern = re.compile(
            r"Location:\s*([\d\.\-]+),\s*([\d\.\-]+)\s*\|\s*Direction:\s*(\d+)[^\d]*\(([^)]+)\)"
        )
        self.location: Optional[Tuple[float, float]] = (None, None)
        self.direction: Optional[int] = None
        self.general_direction: Optional[str] = None

        self.reader_running = False

    def read_logcat(self) -> None:
        """
        Reads and processes ADB logcat output to extract device location and direction data.

        This method continuously reads logcat output, matches the location and direction data
        using the regex pattern, and updates the class attributes accordingly.
        """
        try:
            self.reader_running = True

            # Start ADB logcat process
            process = subprocess.Popen(
                ["adb", "logcat", "DeviceLocation:D", "*:S"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                encoding="utf-8",
            )
            # Read and process the output line by line
            for line in process.stdout:
                line = line.strip()
                self._update_attributes_from_line(line)

        except KeyboardInterrupt:
            self.reader_running = False
            print("\nLogcat reading interrupted by user.")
            process.terminate()
            raise RuntimeError("Logcat reading interrupted by user.")
        except Exception as e:
            self.reader_running = False
            print(f"Error: {e}")

    def _update_attributes_from_line(self, line: str) -> None:
        """
        Updates the class attributes if the input line matches the location and direction pattern.

        Args:
            line (str): A line of logcat output to process.
        """
        if match := self.location_pattern.search(line):
            latitude, longitude, direction, general_direction = match.groups()
            self.location = (float(latitude), float(longitude))
            self.direction = int(direction)
            self.general_direction = general_direction.strip()


def main() -> None:
    """
    The main function to instantiate the DeviceLocationReader and start reading logcat output.
    """
    reader = DeviceLocationReader()
    reader.read_logcat()

    try:
        while True:
            reader.print_attributes()
    except KeyboardInterrupt:
        print("\nExiting...")
if __name__ == "__main__":
    main()