# streaming_system.py
from flask import Flask, Response
import cv2
import threading
import time
from queue import Queue
from functools import wraps
from edison.components.vision_processor.vision_processor import VisionProcessor

class StreamManager:
    def __init__(self, video_source="/dev/video0"):
        self.app = Flask(__name__)
        self.video_source = video_source
        self.frame_queue = Queue(maxsize=2)
        self.lock = threading.Lock()
        self._running = False
        self.app.add_url_rule('/video_feed', 'video_feed', self._video_feed)

    def _video_feed(self):
        return Response(self._generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def _generate_frames(self):
        while self._running:
            with self.lock:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get()
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               buffer.tobytes() + b'\r\n')
            time.sleep(0.05)

    def _capture_frames(self):
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            print(f"Error: Could not open video source {self.video_source}.")
            return
        
        while self._running:
            ret, frame = cap.read()
            if ret:
                with self.lock:
                    while not self.frame_queue.empty():
                        self.frame_queue.get()
                    self.frame_queue.put(frame)
        cap.release()

    def start_stream(self, host='0.0.0.0', port=5000):
        self._running = True
        threading.Thread(target=self._capture_frames, daemon=True).start()
        self.app.run(host=host, port=port, threaded=False)

    def stop(self):
        self._running = False

if __name__ == "__main__":
    streamer = StreamManager()
    streamer.start_stream()
