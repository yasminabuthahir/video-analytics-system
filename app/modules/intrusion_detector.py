import cv2
from datetime import datetime


class IntrusionDetector:
    def __init__(self, roi):
            def flatten(obj):
                """Recursively flatten any nested list to plain integers."""
                if isinstance(obj, list):
                    for item in obj:
                        yield from flatten(item)
                else:
                    yield int(obj)

            flat = list(flatten(roi))
            # flat is now [x1,y1, x2,y2, x3,y3, ...] — all coordinates in order
            xs = flat[0::2]
            ys = flat[1::2]
            self.roi = [min(xs), min(ys), max(xs), max(ys)]
            self.alerts = []

    def _is_inside_roi(self, bbox):
        px1, py1, px2, py2 = bbox
        rx1, ry1, rx2, ry2 = self.roi
        cx = (px1 + px2) // 2
        cy = (py1 + py2) // 2
        return rx1 < cx < rx2 and ry1 < cy < ry2

    def run(self, frame, detections):
        rx1, ry1, rx2, ry2 = self.roi
        cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 0, 255), 2)
        cv2.putText(frame, "Restricted Zone", (rx1, ry1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        intruders = []
        for d in detections:
            if d["label"] == "person" and self._is_inside_roi(d["bbox"]):
                intruders.append(d)
                x1, y1, x2, y2 = d["bbox"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(frame, "INTRUDER", (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        alert = None
        if intruders:
            alert = {
                "type": "intrusion",
                "timestamp": datetime.now().isoformat(),
                "count": len(intruders)
            }
            self.alerts.append(alert)

        return frame, {"intrusion_alert": alert, "intruder_count": len(intruders)}