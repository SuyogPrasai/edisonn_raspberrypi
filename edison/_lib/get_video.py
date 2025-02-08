import subprocess
import os
import time

class GetWebcam:
    def __init__(self):
        self.droidcam_process = None
        self.device_path = None

    def get_webcam(self):
        """Start DroidCam and return video device path"""
        try:
            # Start DroidCam in background
            self.droidcam_process = subprocess.Popen(
                ["droidcam-cli", "adb", "4747"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Find device with retries
            self.device_path = self._find_droidcam_device()
            return self.device_path

        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def _find_droidcam_device(self, max_retries=5):
        """Identify DroidCam's video device by checking device names"""
        for _ in range(max_retries):
            time.sleep(1)  # Wait for device initialization
            video_devices = [f"/dev/{d}" for d in os.listdir("/dev") if d.startswith("video")]
            
            for device in video_devices:
                sys_name = f"/sys/class/video4linux/{os.path.basename(device)}/name"
                if os.path.exists(sys_name):
                    with open(sys_name, "r") as f:
                        if "droidcam" in f.read().lower():
                            return device
        return None

    def stop(self):
        """Stop DroidCam process"""
        if self.droidcam_process:
            self.droidcam_process.terminate()

# Usage example
if __name__ == "__main__":
    webcam = GetWebcam()
    device = webcam.get_webcam()
    
    if device:
        print(f"DroidCam video stream at: {device}")
    else:
        print("Failed to find DroidCam device")