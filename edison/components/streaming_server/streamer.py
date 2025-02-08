# streaming_server.py
from flask import Flask, Response
import cv2
import threading
import time
from queue import Queue

app = Flask(__name__)

class VideoStreamer:
    def __init__(self, max_queue_size=2):
        self.frame_queue = Queue(maxsize=max_queue_size)
        self.latest_frame = None
        self.lock = threading.Lock()
        self._running = True

        # Start background thread to process frames
        self.thread = threading.Thread(target=self._update_frame, daemon=True)
        self.thread.start()

    def _update_frame(self):
        while self._running:
            if not self.frame_queue.empty():
                with self.lock:
                    self.latest_frame = self.frame_queue.get()
                    # Clear queue to only keep latest frame
                    while not self.frame_queue.empty():
                        self.frame_queue.get()

    def add_frame(self, frame):
        """Call this from your processing class with each new frame"""
        try:
            self.frame_queue.put(frame.copy(), block=False)
        except:
            pass  # Drop frame if queue full

    def get_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()

    def stop(self):
        self._running = False
        self.thread.join()

def gen_frames():
    streamer = app.config['streamer']
    while True:
        frame = streamer.get_frame()
        if frame is not None:
            # Convert frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        else:
            time.sleep(0.01)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def run_server():
    app.config['streamer'] = VideoStreamer()
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    run_server()