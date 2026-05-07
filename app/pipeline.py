import sqlite3
import json
import os
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

        # Load YOLO
        self.yolo = YOLO(cam_config["model_path"])

        # Init enabled modules
        self.people_counter = PeopleCounter() if self.modules_cfg.get("people_counter") else None

        roi = cam_config.get("intrusion_roi", [0, 0, 100, 100])
        self.intrusion_detector = IntrusionDetector(roi) if self.modules_cfg.get("intrusion_detector") else None

        self.face_recognizer = FaceRecognizer(
            known_faces_dir=face_config["known_faces_dir"],
            similarity_threshold=face_config["similarity_threshold"]
        ) if self.modules_cfg.get("face_recognizer") else None

        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT,
                alert_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _save_alert(self, alert_type: str, data: dict, timestamp: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO alerts (camera_id, alert_type, data, timestamp) VALUES (?, ?, ?, ?)",
            (self.cam_id, alert_type, json.dumps(data), timestamp)
        )
        conn.commit()
        conn.close()

    def process_frame(self, frame):
        results_summary = {}

        # YOLO detection — person class only (class 0)
        yolo_results = self.yolo(frame, classes=[0], conf=self.conf_threshold, verbose=False)
        detections = []
        for r in yolo_results:
            for box in r.boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                detections.append({
                    "label": "person",
                    "confidence": float(box.conf[0]),
                    "bbox": [x1, y1, x2, y2]
                })

        # People counter
        if self.people_counter:
            frame, data = self.people_counter.run(frame, detections)
            results_summary["people_counter"] = data

        # Intrusion detector
        if self.intrusion_detector:
            frame, data = self.intrusion_detector.run(frame, detections)
            results_summary["intrusion_detector"] = data
            if data.get("intrusion_alert"):
                self._save_alert("intrusion", data, data["intrusion_alert"]["timestamp"])

        # Face recognizer (includes privacy masking)
        if self.face_recognizer:
            frame, data = self.face_recognizer.run(frame)
            results_summary["face_recognizer"] = data

        return frame, results_summary