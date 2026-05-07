import os
import cv2
import torch
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
from app.modules.privacy_masker import PrivacyMasker


class FaceRecognizer:
    def __init__(self, known_faces_dir: str, similarity_threshold: float = 0.7):
        self.device = torch.device("cpu")
        self.mtcnn = MTCNN(keep_all=True, device=self.device, margin=20)
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
        self.threshold = similarity_threshold
        self.privacy_masker = PrivacyMasker()
        self.known_embeddings = {}
        self._load_known_faces(known_faces_dir)

    def _load_known_faces(self, directory: str):
        if not os.path.exists(directory):
            print(f"[FaceRecognizer] known_faces dir not found: {directory}")
            return
        for filename in os.listdir(directory):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(directory, filename)
                img = Image.open(img_path).convert("RGB")
                face_tensor = self.mtcnn(img)
                if face_tensor is not None:
                    if face_tensor.ndim == 3:
                        face_tensor = face_tensor.unsqueeze(0)
                    with torch.no_grad():
                        embedding = self.resnet(face_tensor.to(self.device))
                    self.known_embeddings[name] = embedding[0]
                    print(f"[FaceRecognizer] Registered: {name}")

    def _cosine_similarity(self, a, b):
        return torch.nn.functional.cosine_similarity(
            a.unsqueeze(0), b.unsqueeze(0)
        ).item()

    def run(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        boxes, _ = self.mtcnn.detect(pil_img)
        face_locations = []
        results = []

        if boxes is not None:
            face_tensors = self.mtcnn(pil_img)
            if face_tensors is not None:
                if face_tensors.ndim == 3:
                    face_tensors = face_tensors.unsqueeze(0)
                with torch.no_grad():
                    embeddings = self.resnet(face_tensors.to(self.device))

                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = [int(v) for v in box]
                    face_locations.append([x1, y1, x2, y2])
                    label = "Unknown"

                    if self.known_embeddings:
                        best_score = -1
                        best_name = "Unknown"
                        for name, known_emb in self.known_embeddings.items():
                            score = self._cosine_similarity(embeddings[i], known_emb)
                            if score > best_score:
                                best_score = score
                                best_name = name
                        if best_score >= self.threshold:
                            label = best_name
                        else:
                            label = "Unknown"

                    results.append({"name": label, "bbox": [x1, y1, x2, y2]})

        # Apply privacy masking to ALL detected faces
        frame = self.privacy_masker.run(frame, face_locations)

        # Draw labels after masking
        for r in results:
            x1, y1, x2, y2 = r["bbox"]
            color = (255, 165, 0) if r["name"] != "Unknown" else (128, 128, 128)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, r["name"], (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return frame, {"faces": results, "face_count": len(results)}