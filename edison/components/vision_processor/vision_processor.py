import cv2

class VisionProcessor:
    def get_frame(self, video_source="/dev/video0"):
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
