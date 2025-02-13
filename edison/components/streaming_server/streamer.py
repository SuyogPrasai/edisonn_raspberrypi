# streaming_system.py
from flask import Flask, Response
import cv2
import threading
import time
from queue import Queue
from functools import wraps
from edison.components.vision_processor.vision_processor import VisionProcessor


# Take in a frame
# UPdate the thing in the flask server
# Is there a readymade thing for the various view which the car provides
# Something of that kind ? and then we can passt he frame to multiple things or at least the current direction stuff, speed and the detection frame, only one frame is to be loaded at a timem



class StreamManager:
    def __init__(self):
        self.app = Flask(__name__)
        self.processors = []
        self.frame_queue = Queue(maxsize=2)
        self.lock = threading.Lock()
        self._running = False
        
        # Route setup
        self.app.add_url_rule('/video_feed', 'video_feed', self._video_feed)

    def stream_processor(self, name=None, parallel=True):
        """Decorator to register processing functions"""
        def decorator(func):
            @wraps(func)
            def wrapper(frame):
                return func(frame)
            
            self.processors.append({
                'name': name or func.__name__,
                'func': wrapper,
                'parallel': parallel
            })
            return wrapper
        return decorator

    def _video_feed(self):
        return Response(self._generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')

    def _generate_frames(self):
        while self._running:
            if not self.frame_queue.empty():
                with self.lock:
                    frame = self.frame_queue.get()
                    while not self.frame_queue.empty():  # Keep only latest
                        self.frame_queue.get()
                
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + 
                          buffer.tobytes() + b'\r\n')
            else:
                time.sleep(0.01)

    def _process_frame(self, frame):
        """Execute all processing functions"""
        results = {}
        processed_frame = frame.copy()
        
        for processor in self.processors:
            if processor['parallel']:
                # Start parallel processing thread
                threading.Thread(
                    target=self._run_processor,
                    args=(processor, frame.copy()),
                    daemon=True
                ).start()
            else:
                # Run sequential processing
                processed_frame = processor['func'](processed_frame)
        
        return processed_frame

    def _run_processor(self, processor, frame):
        """Run processor and handle output"""
        result = processor['func'](frame)
        if result is not None:
            self._add_to_stream(result)

    def _add_to_stream(self, frame):
        """Thread-safe frame addition"""
        try:
            self.frame_queue.put(frame, block=False)
        except:
            pass

    def start_stream(self, camera_index=0, host='0.0.0.0', port=5000):
        """Start the streaming system"""
        self._running = True
        
        # Camera capture thread
        def capture_frames():
            cap = cv2.VideoCapture(camera_index)
            while self._running:
                ret, frame = cap.read()
                if ret:
                    processed = self._process_frame(frame)
                    self._add_to_stream(processed)
            cap.release()
        
        threading.Thread(target=capture_frames, daemon=True).start()
        self.app.run(host=host, port=port, threaded=True)

    def stop(self):
        """Graceful shutdown"""
        self._running = False

# Example usage with VisionProcessor integration
if __name__ == "__main__":
    streamer = StreamManager()
    vp = VisionProcessor()  # Your existing VisionProcessor class

    # Register processing functions
    @streamer.stream_processor(name="object_detection", parallel=False)
    def detect_objects(frame):
        processed_frame, _ = vp.process_frame(frame)
        return processed_frame

    @streamer.stream_processor(name="grayscale", parallel=True)
    def grayscale_version(frame):
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Start the stream with both processors
    streamer.start_stream()