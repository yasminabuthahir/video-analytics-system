import cv2
import threading
import time


class CameraStream:
    def __init__(self, camera_id: str, source):
        self.camera_id = camera_id
        self.source = source
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        src = self.source if isinstance(self.source, int) else str(self.source)
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            print(f"[CameraStream] Cannot open source: {self.source}")
            return False
        self.running = True
        thread = threading.Thread(target=self._read_loop, daemon=True)
        thread.start()
        print(f"[CameraStream] Started: {self.camera_id} ({self.source})")
        return True

    def _read_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            with self.lock:
                self.frame = frame
            time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def get_snapshot(self):
        """Returns a single JPEG-encoded frame for the ROI tool."""
        frame = self.get_frame()
        if frame is None:
            return None
        _, buf = cv2.imencode(".jpg", frame)
        return buf.tobytes()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()