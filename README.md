# video-analytics-system
Multi-Application Video Analytics System
video-analytics-system/
├── config.json
├── main.py
├── requirements.txt
├── Dockerfile
├── README.md
├── app/
│   ├── camera_manager.py
│   ├── pipeline.py
│   ├── api.py
│   └── modules/
│       ├── people_counter.py
│       ├── intrusion_detector.py
│       ├── face_recognizer.py
│       └── privacy_masker.py
├── models/
│   └── (YOLO weights go here)
├── known_faces/
│   └── (face images for registration)
└── outputs/
    └── (alert logs, snapshots)