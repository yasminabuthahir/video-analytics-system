import cv2


class PeopleCounter:
    def __init__(self):
        self.count = 0

    def run(self, frame, detections):
        persons = [d for d in detections if d["label"] == "person"]
        self.count = len(persons)

        for p in persons:
            x1, y1, x2, y2 = p["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, "Person", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.putText(frame, f"Count: {self.count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return frame, {"people_count": self.count}