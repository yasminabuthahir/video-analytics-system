# 🎥 Video Analytics System

A production-grade, multi-camera intelligent video analytics platform built with Python, FastAPI, YOLOv8, FaceNet, and React. Designed for real-world deployment on edge hardware (RKNN/Ambarella boards) and standard CPU/GPU machines.

---

## 📸 Demo

> `[▶ Watch Demo](https://youtube.com/your-link-here)`

---

## ✨ Features

### 🔍 Analytics Modules
| Module | Description |
|---|---|
| **People Counter** | Detects and counts persons in frame using YOLOv8 |
| **Intrusion Detector** | Alerts when a person enters a user-defined restricted zone |
| **Face Recognition** | Identifies registered individuals using FaceNet embeddings |
| **Person Re-Identification** | Tracks identity across camera views using OSNet |
| **Privacy Masker** | Automatically blurs all detected faces in the output frame |
| **OCR Pipeline** | Extracts vehicle number plates using YOLOv8 + PaddleOCR |
| **Age & Gender Classification** | Classifies detected persons using ResNet-50 |

### 🖥️ System Capabilities
- **Multi-camera support** — run multiple cameras concurrently, each with independent module configuration
- **Config-driven architecture** — single `config.json` controls all cameras, modules, model paths, ROI zones, and API ports
- **Runtime hot-reload** — toggle modules and update ROI zones from the frontend without restarting the backend
- **Edge deployment ready** — packaged for RKNN and Ambarella NPU/CPU/GPU boards running Linux
- **REST API** — FastAPI backend exposes detection results, alert history, and config endpoints
- **Alert persistence** — intrusion alerts saved to SQLite with timestamp, person label, people count, and JPEG snapshot
- **Role-based auth** — JWT authentication with admin and viewer roles

### 🎨 Frontend (React)
- Login with configurable backend URL — connect to any IP:port on your network
- Live dashboard — real-time people count, face count, active cameras
- Camera configuration — toggle modules per camera with live toggle switches
- **Polygon ROI drawing** — draw restricted zones directly on a live camera frame fetched from the backend; coordinates auto-scaled to match actual frame resolution
- Alert history table — full alert log with inline snapshots
- User management — admin can create and delete users (admin only)

---

## 🗂️ Project Structure

```
video-analytics-system/
├── main.py                        # Entry point — starts camera threads + FastAPI server
├── config.json                    # Master config for all cameras and modules
├── requirements.txt
├── Dockerfile
├── app/
│   ├── api.py                     # FastAPI routes — auth, alerts, config, frame snapshot
│   ├── auth.py                    # JWT auth, bcrypt password hashing, user DB
│   ├── camera_manager.py          # Per-camera stream thread with RTSP/MP4/webcam support
│   ├── pipeline.py                # Per-camera inference pipeline with hot-reload support
│   └── modules/
│       ├── people_counter.py      # YOLOv8 person counting
│       ├── intrusion_detector.py  # ROI-based intrusion detection
│       ├── face_recognizer.py     # FaceNet embedding-based recognition
│       └── privacy_masker.py      # Gaussian blur face masking
├── models/                        # YOLOv8 weights (auto-downloaded on first run)
├── known_faces/                   # Registration images — one photo per person (name.jpg)
├── media/                         # Intrusion alert snapshots (JPEG)
├── outputs/
│   ├── alerts.db                  # SQLite — alert log
│   └── auth.db                    # SQLite — user credentials
└── frontend/                      # React + Vite frontend
    └── src/
        ├── pages/
        │   ├── Login.jsx
        │   ├── Dashboard.jsx
        │   ├── CameraConfig.jsx
        │   ├── AlertHistory.jsx
        │   └── UserManagement.jsx
        └── components/
            ├── Navbar.jsx
            └── ROIDrawer.jsx      # Polygon ROI tool on live camera frame
```

---

## ⚙️ Tech Stack

**Backend**
- Python 3.10
- FastAPI + Uvicorn
- YOLOv8 (Ultralytics) — person, object, fire detection
- FaceNet (facenet-pytorch) — face recognition via embedding similarity
- OSNet — person re-identification
- ResNet-50 / MobileNet — age & gender classification
- PaddleOCR — number plate text extraction
- OpenCV — video stream handling, frame annotation
- SQLite — alert and auth storage
- JWT (python-jose) + bcrypt (passlib) — authentication

**Frontend**
- React 18 + Vite
- React Router DOM
- Axios
- Lucide React (icons)

**Deployment**
- Linux (Ubuntu 22.04)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Linux recommended (tested on Ubuntu 22.04)

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/yasminabuthahir/video-analytics-system.git
cd video-analytics-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p models outputs media known_faces

# Add known faces (optional — for face recognition)
# Place one clear face photo per person in known_faces/
# Name the file as the person's name: yasmin.jpg, john.jpg etc.

# Run
python3 main.py
```

Backend starts at: `http://0.0.0.0:8000`  

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at: `http://localhost:5173`

On the login page, set the **Backend URL** to:
- `http://localhost:8000` — if running on the same machine
- `http://192.168.x.x:8000` — to connect from another device on the same network

---

## 📷 Camera Configuration

Edit `config.json` to add cameras:

```json
{
  "cameras": [
    {
      "camera_id": "cam_01",
      "name": "Front Entrance",
      "source": "test_video.mp4",
      "enabled": true,
      "modules": {
        "people_counter": true,
        "intrusion_detector": true,
        "face_recognizer": true,
        "privacy_masker": true
      },
      "intrusion_roi": [100, 100, 500, 400],
      "model_path": "models/yolov8n.pt",
      "confidence_threshold": 0.5
    }
  ]
}
```

**Source formats supported:**
| Format | Example |
|---|---|
| Video file | `"test_video.mp4"` |
| RTSP stream | `"rtsp://192.168.1.100:554/stream"` |
| Webcam | `0` |

**ROI Zones** can also be drawn interactively from the frontend — navigate to **Cameras → Edit ROI**, draw a polygon on the live camera frame, and save. Changes apply instantly without restarting.

---

## 🔐 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | None | Login, returns JWT token |
| GET | `/status` | Any | Live camera status and detection results |
| GET | `/alerts` | Any | Alert history with snapshots |
| GET | `/count/{camera_id}` | Any | Current people count for a camera |
| GET | `/cameras/{camera_id}/frame` | Any | Fetch one frame (for ROI tool) |
| GET | `/config` | Any | Read current config.json |
| POST | `/config/modules` | Admin | Toggle modules per camera (hot-reload) |
| POST | `/config/roi` | Admin | Update ROI polygon (hot-reload) |
| DELETE | `/config/roi` | Admin | Delete an ROI zone |
| POST | `/config/source` | Admin | Update camera source |
| GET | `/users` | Admin | List all users |
| POST | `/users` | Admin | Create a user |
| DELETE | `/users/{username}` | Admin | Delete a user |

---

## 🗃️ Alert Schema

Each intrusion alert stored in SQLite contains:

| Field          | Description                                |
|----------------|------------------------------------------- |
| `id`           | Auto-increment alert ID                    |
| `camera_id`    | Which camera triggered the alert           |
| `alert_type`   | `"intrusion"`                              |
| `people_count` | Number of people in the restricted zone    |
| `person_label` | Name if recognized, `"Unknown"` otherwise  |
| `timestamp`    | ISO 8601 datetime                          |
| `snapshot_path`| Path to saved JPEG in `/media`             |

---

## 🧠 How It Works

```
config.json
    │
    ▼
CameraStream (thread per camera)
    │  reads frames from MP4 / RTSP / webcam
    ▼
Pipeline (thread per camera)
    │
    ├── YOLOv8 ──► person detections
    │
    ├── PeopleCounter ──► count persons in frame
    │
    ├── IntrusionDetector ──► check if person center is inside ROI polygon
    │       └── if yes ──► save alert + snapshot to DB + /media
    │
    ├── FaceRecognizer (FaceNet) ──► match against known_faces embeddings
    │
    └── PrivacyMasker ──► Gaussian blur all detected faces
    │
    ▼
frames_ref (shared dict)
    │
    ├── DisplayThread ──► cv2.imshow per camera window
    │
    └── FastAPI ──► /status, /alerts, /count, /frame endpoints
                        │
                        ▼
                  React Frontend
```
---

## 📋 Requirements

```
ultralytics==8.2.0
facenet-pytorch==2.5.3
fastapi==0.111.0
uvicorn==0.30.1
opencv-python==4.10.0.84
numpy==1.26.4
torch==2.3.0
torchvision==0.18.0
Pillow==10.3.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
aiofiles==23.2.1
```
---

## 👩‍💻 Author

**Yasmin A**  
AI Engineer — Computer Vision & Edge Deployment  
[LinkedIn](https://www.linkedin.com/in/yasmin-abuthahir) · [GitHub](https://github.com/yasminabuthahir)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
