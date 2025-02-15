import cv2

class VisionProcessor:

    def capture_frame(self):
        cap = cv2.VideoCapture(0)  # Open the default camera
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return None
        
        ret, frame = cap.read()  # Capture a frame
        cap.release()  # Release the camera
        
        if not ret:
            print("Error: Could not read frame.")
            return None
        
        return frame
