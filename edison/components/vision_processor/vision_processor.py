import cv2
import numpy as np
import torch
from pathlib import Path
from typing import Tuple, Dict, List, Union

class VisionProcessor:
    def __init__(self, camera_index: Union[int, str] = 0):  # Accept both camera index and file path
        self._load_calibration()
        self._init_models()
        self._init_video(camera_index)  # Initialize video source here
        
        # ROI parameters
        self.roi_ratio = (0.4, 0.8)
        self.depth_scale = 0.1

    def _load_calibration(self) -> None:
        try:
            # Replace with actual calibration data for your camera
            self.mtx = np.array([[1000, 0, 640], [0, 1000, 360], [0, 0, 1]], dtype=np.float32)
            self.dist = np.zeros((1, 5), dtype=np.float32)
        except Exception as e:
            raise

    def _init_models(self) -> None:
        try:
            # Use smaller YOLOv5n model for faster inference
            self.obj_model = torch.hub.load('ultralytics/yolov5', 'yolov5n', 
                                          pretrained=True, force_reload=False)
            self.obj_model.classes = [0, 1, 2, 3, 5, 7]  # Person, vehicles
            self.obj_model.conf = 0.45
            
            # Initialize depth estimation
            self.depth_model = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
            self.depth_model.eval()
            
            self.logger.info("Models initialized")
        except Exception as e:
            self.logger.error(f"Model initialization failed: {str(e)}")
            raise

    def _init_video(self, video_source: Union[str, int]) -> None:
        self.cap = cv2.VideoCapture(video_source)
        if not self.cap.isOpened():
            self.logger.error(f"Failed to open video source: {video_source}")
            raise RuntimeError("Video initialization failed")

        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.logger.info(f"Video initialized: {self.frame_width}x{self.frame_height} @ {self.fps:.2f} FPS")

    def process_webcam(self) -> None:
        """Process real-time webcam feed"""
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Failed to capture frame")
                continue

            processed_frame, _ = self.process_frame(frame)
            cv2.imshow("Real-time Processing", processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.release()

    def catch_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Faled to parse frame")
            return frame
        
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        try:
            frame_undist = cv2.undistort(frame, self.mtx, self.dist)
            roi = self._apply_roi(frame_undist)
            
            obstacle_data = self._detect_obstacles(roi)
            lane_data = self._detect_lanes(roi)
            
            visualized = self._visualize_results(frame_undist, obstacle_data, lane_data)
            return visualized, obstacle_data, lane_data
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            return frame, []

    # Keep other helper methods the same (_apply_roi, _detect_obstacles, etc.)

if __name__ == "__main__":
    try:
        # For webcam use (default camera)
        processor = VisionProcessor(camera_index=2)
        processor.process_webcam()
    except Exception as e:
        print(f"Fatal error: {str(e)}")