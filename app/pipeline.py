import sqlite3
import json
import os
import cv2
import threading
from datetime import datetime
from ultralytics import YOLO
from app.modules.people_counter import PeopleCounter
from app.modules.intrusion_detector import IntrusionDetector
from app.modules.face_recognizer import FaceRecognizer


class Pipeline:
    def __init__(self, cam_config: dict, face_config: dict, db_path: str):
        self.cam_id = cam_config["camera_id"]
        self.modules_cfg = cam_config["modules"]
        self.conf_threshold = cam_config.get("confidence_threshold", 0.5)
        self.db_path = db_path
        self.media_dir = "media"
        self.lock = threading.Lock()
        os.makedirs(self.media_dir, exist_ok=True)

        model_path = cam_config["model_path"]
        if not os.path.exists(model_path):
            print(f"[Pipeline] Downloading YOLO model to {model_path}...")
        self.yolo = YOLO(model_path)

        self.roi = cam_config.get("intrusion_roi", None)
        self.face_config = face_config
        self._init_modules()
        self._init_db()

    def _init_modules(self):
        self.people_counter = (
            PeopleCounter() if self.modules_cfg.get("people_counter") else None
        )
        self.intrusion_detector = (
            IntrusionDetector(self.roi)
            if self.modules_cfg.get("intrusion_detector") and self.roi
            else None
        )
        self.face_recognizer = (
            FaceRecognizer(
                known_faces_dir=self.face_config["known_faces_dir"],
                similarity_threshold=self.face_config["similarity_threshold"]
            )
            if self.modules_cfg.get("face_recognizer")
            else None
        )

    def update_modules(self, new_modules: dict):
        """Hot-reload modules from frontend toggle — no restart needed."""
        with self.lock:
            self.modules_cfg.update(new_modules)
            self._init_modules()

    def update_roi(self, new_roi: list):
        """Hot-reload ROI — updates intrusion detector in place."""
        with self.lock:
            self.roi = new_roi
            if self.modules_cfg.get("intrusion_detector"):
                self.intrusion_detector = IntrusionDetector(new_roi)

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT,
                alert_type TEXT,
                people_count INTEGER,
                person_label TEXT,
                timestamp TEXT,
                snapshot_path TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _save_snapshot(self, frame):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.cam_id}_{ts}.jpg"
        path = os.path.join(self.media_dir, filename)
        cv2.imwrite(path, frame)
        return path

    def _save_alert(self, alert_type, people_count, person_label, timestamp, snapshot_path):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO alerts
               (camera_id, alert_type, people_count, person_label, timestamp, snapshot_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (self.cam_id, alert_type, people_count, person_label, timestamp, snapshot_path)
        )
        conn.commit()
        conn.close()

    def process_frame(self, frame):
        with self.lock:
            results_summary = {}

            yolo_results = self.yolo(
                frame, classes=[0], conf=self.conf_threshold, verbose=False
            )
            detections = []
            for r in yolo_results:
                for box in r.boxes:
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                    detections.append({
                        "label": "person",
                        "confidence": float(box.conf[0]),
                        "bbox": [x1, y1, x2, y2]
                    })

            if self.people_counter:
                frame, data = self.people_counter.run(frame, detections)
                results_summary["people_counter"] = data

            face_labels = []
            if self.face_recognizer:
                frame, face_data = self.face_recognizer.run(frame)
                results_summary["face_recognizer"] = face_data
                face_labels = [f["name"] for f in face_data.get("faces", [])]

            if self.intrusion_detector:
                frame, data = self.intrusion_detector.run(frame, detections)
                results_summary["intrusion_detector"] = data
                if data.get("intrusion_alert"):
                    snapshot_path = self._save_snapshot(frame)
                    people_count = data.get("intruder_count", 0)
                    person_label = ", ".join(face_labels) if face_labels else "Unknown"
                    timestamp = data["intrusion_alert"]["timestamp"]
                    self._save_alert(
                        "intrusion", people_count, person_label,
                        timestamp, snapshot_path
                    )

            return frame, results_summary