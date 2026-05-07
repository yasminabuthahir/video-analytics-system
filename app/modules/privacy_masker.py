import cv2


class PrivacyMasker:
    def run(self, frame, face_locations):
        """
        face_locations: list of [x1, y1, x2, y2] for each detected face
        Applies a blur over each face region.
        """
        for (x1, y1, x2, y2) in face_locations:
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            if x2 > x1 and y2 > y1:
                face_region = frame[y1:y2, x1:x2]
                blurred = cv2.GaussianBlur(face_region, (51, 51), 30)
                frame[y1:y2, x1:x2] = blurred
        return frame