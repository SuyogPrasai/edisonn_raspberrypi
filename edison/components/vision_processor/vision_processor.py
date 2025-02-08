import cv2
import numpy as np
import torch
from collections import deque

class VisionProcessor:
    def __init__(self):
        # YOLOv5 Model Setup
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.classes = [0, 1, 2, 3, 5, 7]  # Person, vehicle classes
        self.obstacles = []
        
        # Lane Detection Parameters
        self.lane_history = deque(maxlen=5)  # Smoothing lane detection
        self.roi_vertices = np.array([[(0, 720), (1280//2-150, 450), 
                                     (1280//2+150, 450), (1280, 720)]], dtype=np.int32)
        
        # Camera Calibration (Example values - should calibrate for your camera)
        self.mtx = np.array([[1.15777930e+03, 0.00000000e+00, 6.67111054e+02],
                            [0.00000000e+00, 1.15282291e+03, 3.86128937e+02],
                            [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
        self.dist = np.array([-0.24688807, -0.02373117, -0.00109837, 0.00035108, -0.00259172])

    def process_frame(self, frame):
        # Undistort frame
        frame = cv2.undistort(frame, self.mtx, self.dist, None, self.mtx)
        
        # Process obstacles
        obstacle_frame = self._detect_obstacles(frame)
        
        # Process lanes
        lane_frame = self._detect_lanes(frame)
        
        # Combine results
        combined = cv2.addWeighted(obstacle_frame, 0.6, lane_frame, 0.4, 0)
        
        # Add info overlay
        combined = self._add_overlay(combined)
        
        return combined, self.obstacles

    def _detect_obstacles(self, frame):
        results = self.model(frame)
        self.obstacles = []
        
        for det in results.xyxy[0]:
            x1, y1, x2, y2, conf, cls = det.cpu().numpy()
            self.obstacles.append({
                'type': self.model.names[int(cls)],
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'confidence': float(conf),
                'distance': self._estimate_distance(y2)
            })
            
        return results.render()[0]

    def _estimate_distance(self, y2):
        # Simple perspective-based distance estimation
        return 0.1 * (720 - y2) ** 1.5  # Empirical formula (calibrate for your setup)

    def _detect_lanes(self, frame):
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blur, 50, 150)
        
        # ROI mask
        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, self.roi_vertices, 255)
        masked_edges = cv2.bitwise_and(edges, mask)
        
        # Hough Transform
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, 50, 
                               minLineLength=50, maxLineGap=30)
        
        # Lane processing
        lane_img = np.zeros_like(frame)
        if lines is not None:
            left_lines, right_lines = self._separate_lines(lines)
            
            # Average and extrapolate lines
            left_lane = self._average_lines(left_lines)
            right_lane = self._average_lines(right_lines)
            
            # Add to history
            self.lane_history.append((left_lane, right_lane))
            
            # Draw lanes
            self._draw_lanes(lane_img)
            
        return lane_img

    def _separate_lines(self, lines):
        left = []
        right = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            slope = (y2 - y1) / (x2 - x1 + 1e-5)
            
            if abs(slope) < 0.5:  # Horizontal lines
                continue
                
            if slope < 0:
                left.append((slope, line[0]))
            else:
                right.append((slope, line[0]))
                
        return left, right

    def _average_lines(self, lines):
        if not lines:
            return None
            
        slopes = [slope for slope, _ in lines]
        lines = [line for _, line in lines]
        
        avg_slope = np.mean(slopes)
        avg_line = np.mean(lines, axis=0)
        
        # Extrapolate line to bottom and middle of ROI
        y1 = self.roi_vertices[0][1][1]  # Bottom of ROI
        y2 = self.roi_vertices[0][0][1]  # Top of ROI
        
        x1 = int(avg_line[0] + (y1 - avg_line[1]) / avg_slope)
        x2 = int(avg_line[0] + (y2 - avg_line[1]) / avg_slope)
        
        return (x1, y1, x2, y2)

    def _draw_lanes(self, img):
        # Use historical average
        lanes = list(self.lane_history)
        left = [l[0] for l in lanes if l[0] is not None]
        right = [l[1] for l in lanes if l[1] is not None]
        
        if left:
            avg_left = np.mean(left, axis=0).astype(int)
            cv2.line(img, (avg_left[0], avg_left[1]), 
                    (avg_left[2], avg_left[3]), (0,255,0), 10)
            
        if right:
            avg_right = np.mean(right, axis=0).astype(int)
            cv2.line(img, (avg_right[0], avg_right[1]), 
                    (avg_right[2], avg_right[3]), (0,255,0), 10)

    def _add_overlay(self, frame):
        # Lane information
        if self.lane_history:
            left, right = self.lane_history[-1]
            if left and right:
                center = (left[0] + right[0]) // 2
                cv2.line(frame, (center, 720), (640, 720), (0,0,255), 5)
        
        # Obstacle info
        for obstacle in self.obstacles:
            x1, y1, x2, y2 = obstacle['bbox']
            cv2.putText(frame, f"{obstacle['type']} {obstacle['distance']:.1f}m",
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
        
        return frame

# Usage Example
if __name__ == "__main__":
    vp = VisionProcessor()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        processed_frame, obstacles = vp.process_frame(frame)
        
        cv2.imshow('Output', processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()