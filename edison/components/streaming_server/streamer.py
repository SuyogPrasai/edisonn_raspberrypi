# streaming_system.py
from flask import Flask, Response
import cv2
import threading
import time
from queue import Queue
from functools import wraps

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
                self.update_frame(frame)
        cap.release()

    def start_stream(self, host='0.0.0.0', port=5000, use_internal_capture=True):
        self._running = True
        if use_internal_capture:
            threading.Thread(target=self._capture_frames, daemon=True).start()
        # Start Flask in a daemon thread
        flask_thread = threading.Thread(target=self.app.run, 
                                     kwargs={'host': host, 'port': port, 'threaded': False},
                                     daemon=True)
        flask_thread.start()

    def stop(self):
        self._running = False

    def update_frame(self, frame):
        with self.lock:
            # Keep only the latest frame
            while not self.frame_queue.empty():
                self.frame_queue.get()
            self.frame_queue.put(frame)

    def frame_decorator(self, func):
        @wraps(func)
        def wrapper(frame):
            processed_frame = func(frame)
            self.update_frame(processed_frame)
            return processed_frame
        return wrapper

if __name__ == "__main__":
    streamer = StreamManager()
    streamer.start_stream()