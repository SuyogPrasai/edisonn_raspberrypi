import cv2

class VisionProcessor:
    def capture_frame(self, video_source=0):
        cap = cv2.VideoCapture(video_source)  # Open the specified video source
        if not cap.isOpened():
            print(f"Error: Could not open video source {video_source}.")
            return None
        
        ret, frame = cap.read()  # Capture a frame
        cap.release()  # Release the video source
        
        if not ret:
            print("Error: Could not read frame.")
            return None
        
        return frame
    

    def capture(self):     
        cap = cv2.VideoCapture(0)  # Or "/dev/video0"
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("test.jpg", frame)
        else:
            print("Failed to capture frame")
        cap.release()

