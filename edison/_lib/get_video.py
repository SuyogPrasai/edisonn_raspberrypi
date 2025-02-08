import subprocess
import threading
import os
import time
from typing import Optional, Set

class WebcamManager:
    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.loopback_device: Optional[str] = None
        self._setup_complete = threading.Event()

    def start_setup(self) -> None:
        """Start webcam setup in a background thread."""
        if self.thread and self.thread.is_alive():
            print("Webcam setup already in progress")
            return
        
        self.thread = threading.Thread(target=self._setup_webcam, daemon=True)
        self.thread.start()

    def _check_adb_connection(self) -> None:
        """Verify ADB connection has authorized devices."""
        result = subprocess.run(
            ["adb", "devices"],
            check=True,
            capture_output=True,
            text=True
        )
        if "device" not in result.stdout:
            raise RuntimeError("No authorized ADB devices connected")

    def _load_v4l2loopback(self) -> None:
        """Load v4l2loopback kernel module."""
        try:
            subprocess.run(
                ["modprobe", "v4l2loopback"],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to load v4l2loopback module: {e.stderr.strip()}")

    def _get_video_devices(self) -> Set[str]:
        """Get set of available video devices."""
        video_dir = "/sys/class/video4linux"
        return set(os.listdir(video_dir)) if os.path.exists(video_dir else set()

    def _detect_loopback_device(self, before: Set[str], after: Set[str]) -> Optional[str]:
        """Identify new v4l2loopback device."""
        new_devices = after - before
        for dev in new_devices:
            dev_path = os.path.join("/sys/class/video4linux", dev)
            name_file = os.path.join(dev_path, "name")
            
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    if "v4l2 loopback" in f.read().strip():
                        return f"/dev/{dev}"
        return None

    def _start_droidcam(self) -> None:
        """Start DroidCam streaming."""
        print("Starting DroidCam... (Ctrl+C to stop)")
        subprocess.run(
            ["droidcam-cli", "adb", "4747"],
            check=True
        )

    def _setup_webcam(self) -> None:
        """Main setup sequence executed in thread."""
        try:
            self._check_adb_connection()
            
            before = self._get_video_devices()
            self._load_v4l2loopback()
            time.sleep(1)  # Allow time for device creation
            
            after = self._get_video_devices()
            self.loopback_device = self._detect_loopback_device(before, after)
            
            if not self.loopback_device:
                raise RuntimeError("Failed to detect v4l2loopback device")
            
            print(f"Virtual webcam created at: {self.loopback_device}")
            self._setup_complete.set()
            
            self._start_droidcam()
            
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e.stderr.strip() or e.stdout.strip()}")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            self._setup_complete.set()

    def wait_for_device(self, timeout: Optional[float] = None) -> Optional[str]:
        """Block until loopback device is ready or timeout occurs."""
        self._setup_complete.wait(timeout)
        return self.loopback_device

if __name__ == "__main__":
    webcam = WebcamManager()
    webcam.start_setup()
    
    device = webcam.wait_for_device(5)
    if device:
        print(f"Use this device in your apps: {device}")
    else:
        print("Failed to detect webcam device within timeout")