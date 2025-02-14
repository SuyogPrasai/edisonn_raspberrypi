import cv2
import numpy as np
import torch
from collections import deque

class VisionProcessor:
    def __init__(self):
        """
        Optional: If you still want YOLO-based obstacle detection, 
        you can initialize the model here. 
        Otherwise, omit this part.
        """
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        # Example: detect only person, car, etc.
        self.model.classes = [0, 1, 2, 3, 5, 7]
        
        # Camera calibration (if available)
        self.mtx = np.array([
            [1157.7793, 0.0,       667.111054],
            [0.0,       1152.82291, 386.128937],
            [0.0,       0.0,         1.0]
        ])
        self.dist = np.array([-0.24688807, -0.02373117, -0.00109837, 0.00035108, -0.00259172])
        
        self.obstacles = []

    def capture_frame(self):
        """
        Captures a single frame from the video source.
        Returns the captured frame if successful, otherwise None.
        """
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            return None
        return frame
    
    def process_frame(self, frame):
        """
        Main pipeline:
          1) Undistort (optional if you have calibration).
          2) Detect obstacles with YOLOv5 (optional).
          3) Detect road boundaries.
          4) Overlay results and return.
        """
        # 1. Undistort
        frame_undistorted = cv2.undistort(frame, self.mtx, self.dist, None, self.mtx)
        
        # 2. Detect obstacles (optional)
        obstacle_frame = self._detect_obstacles(frame_undistorted)
        
        # 3. Road boundary detection
        boundary_frame = self._detect_road_boundaries(frame_undistorted)
        
        # 4. Combine
        combined = cv2.addWeighted(obstacle_frame, 0.7, boundary_frame, 0.3, 0)
        
        # 5. Overlay text (distance, etc.)
        combined = self._add_overlay(combined)
        
        return combined, self.obstacles

    def _detect_obstacles(self, frame):
        """
        YOLOv5 detection. Renders bounding boxes on the frame.
        """
        results = self.model(frame)
        self.obstacles = []
        
        for det in results.xyxy[0]:
            x1, y1, x2, y2, conf, cls_id = det.cpu().numpy()
            self.obstacles.append({
                'type': self.model.names[int(cls_id)],
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'confidence': float(conf),
                'distance': self._estimate_distance(y2, frame.shape[0])
            })
        
        # Render bounding boxes
        rendered = results.render()[0]
        return rendered

    def _estimate_distance(self, y2, frame_height):
        """
        Dummy perspective-based distance estimation.
        Adjust or calibrate for your setup.
        """
        return 0.1 * (frame_height - y2) ** 1.5

    def _detect_road_boundaries(self, frame):
        """
        Attempt to find the largest "road-like" region by color,
        then approximate the boundary with lines.
        """
        # 1. Convert to HSV (tune these thresholds to match your road color!)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Example: typical asphalt might appear in a certain gray/brown range
        # You MUST tune these for your specific lighting/road color:
        lower_road = np.array([0, 0, 50])    # dummy
        upper_road = np.array([180, 60, 200]) # dummy
        
        mask = cv2.inRange(hsv, lower_road, upper_road)
        
        # 2. Morphological operations to clean up noise
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 3. Find contours; pick the largest
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            # No road detected
            return frame
        
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 4. Approximate the boundary polygon
        epsilon = 0.01 * cv2.arcLength(largest_contour, True)
        approx_poly = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # 5. Draw the polygon or edges onto a blank image
        boundary_img = np.zeros_like(frame)
        cv2.drawContours(boundary_img, [approx_poly], -1, (0, 0, 255), 3)
        
        # Optional: if you want left/right lines, you could do more analysis
        # on the polygon’s points (e.g., find the topmost, bottommost, leftmost, etc.)
        # and draw lines. For now, we just outline the entire region.
        
        return boundary_img

    def _add_overlay(self, frame):
        """
        Overlay obstacle distance info, etc.
        """
        for obstacle in self.obstacles:
            x1, y1, x2, y2 = obstacle['bbox']
            dist_str = f"{obstacle['distance']:.1f}m"
            label = f"{obstacle['type']} {dist_str}"
            cv2.putText(frame, label, (x1, max(0, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return frame


# ------------------- Usage Example ------------------- #
if __name__ == "__main__":
    detector = RoadBoundaryDetector()
    
    # Replace with your video source or image
    cap = cv2.VideoCapture(2)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frame, obstacles = detector.process_frame(frame)
        
        cv2.imshow("Road Boundary Detection", processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
