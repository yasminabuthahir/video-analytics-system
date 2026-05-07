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
        # source: int for webcam, string for file or rtsp
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
                # For video files, loop back to start
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            with self.lock:
                self.frame = frame
            time.sleep(0.01)  # ~100fps cap, CPU friendly

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()