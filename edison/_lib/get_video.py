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
    

        except Exception as e:
            print(f"Error: {str(e)}")
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