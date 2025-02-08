import subprocess
import threading
import os
import time

class GetWebcam:
    def __init__(self):
        self.thread = None
        self.loopback_device = None  # Stores detected device path
        self._setup_complete = threading.Event()  # Signals device detection

    def get_webcam(self):
        """Start webcam setup in a background thread."""
        if self.thread and self.thread.is_alive():
            print("Webcam setup already running")
            return
        self.thread = threading.Thread(target=self._setup_webcam)
        self.thread.start()

    def _get_video_devices(self):
        """List video devices in /sys/class/video4linux."""
        video_dir = "/sys/class/video4linux"
        return set(os.listdir(video_dir)) if os.path.exists(video_dir) else set()

    def _find_loopback_device(self, before, after):
        """Identify newly created v4l2loopback device."""
        for dev in (after - before):
            dev_path = os.path.join("/sys/class/video4linux", dev)
            name_file = os.path.join(dev_path, "name")
            
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    if "v4l2 loopback" in f.read():
                        return f"/dev/{dev}"
        return None

    def _setup_webcam(self):
        """Main setup logic executed in thread."""
        try:
            # 1. Verify ADB connection
            adb_devices = subprocess.run(
                ["adb", "devices"],
                check=True,
                capture_output=True,
                text=True
            )
            if "device" not in adb_devices.stdout:
                raise RuntimeError("No authorized ADB devices connected")

            # 2. Capture existing devices before modprobe
            before_devices = self._get_video_devices()

            # 4. Detect new loopback device
            time.sleep(0.5)  # Allow kernel to create devices
            after_devices = self._get_video_devices()
            self.loopback_device = self._find_loopback_device(before_devices, after_devices)

            if not self.loopback_device:
                raise RuntimeError("Failed to detect v4l2loopback device")

            print(f"Virtual webcam created at: {self.loopback_device}")
            self._setup_complete.set()  # Signal completion

            # 5. Start DroidCam stream
            print("Starting DroidCam... (Ctrl+C to stop)")
            subprocess.run(
                ["droidcam-cli", "adb", "4747"],
                check=True
            )

        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e.stderr.decode().strip()}")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            self._setup_complete.set()  # Ensure event is always set

    def wait_for_device(self, timeout=None):
        """Block until loopback device is detected or timeout occurs."""
        self._setup_complete.wait(timeout)
        return self.loopback_device

# Usage example
if __name__ == "__main__":
    webcam = GetWebcam()
    webcam.get_webcam()
    
    # Wait up to 5 seconds for device detection
    device = webcam.wait_for_device(5)
    if device:
        print(f"Use this device in your apps: {device}")
    else:
        print("Failed to detect webcam device within timeout")