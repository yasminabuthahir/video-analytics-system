import sqlite3
import json
import os
import threading
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List
from app.auth import (
    authenticate_user, create_access_token, decode_token,
    get_all_users, create_user, delete_user, init_auth_db
)

app = FastAPI(title="Video Analytics System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_db_path = None
_auth_db = "outputs/auth.db"
_config_path = "config.json"
_config_lock = threading.Lock()
_pipelines = {}     # camera_id -> Pipeline instance
_streams = {}       # camera_id -> CameraStream instance
_results = {}       # camera_id -> latest summary dict


def init_api(db_path: str, pipelines_ref: dict, streams_ref: dict, results_ref: dict):
    global _db_path, _pipelines, _streams, _results
    _db_path = db_path
    _pipelines = pipelines_ref
    _streams = streams_ref
    _results = results_ref
    init_auth_db(_auth_db)
    if os.path.exists("media"):
        app.mount("/media", StaticFiles(directory="media"), name="media")


def _load_config():
    with _config_lock:
        with open(_config_path) as f:
            return json.load(f)


def _save_config(config):
    with _config_lock:
        with open(_config_path, "w") as f:
            json.dump(config, f, indent=2)


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")
    return payload


def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------- AUTH ----------

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


# ---------- STATUS ----------

@app.get("/status")
def get_status(user=Depends(get_current_user)):
    return {"cameras": [
        {"camera_id": cam_id, "latest": data}
        for cam_id, data in _results.items()
    ]}


# ---------- FRAME SNAPSHOT FOR ROI TOOL ----------

@app.get("/cameras/{camera_id}/frame")
def get_camera_frame(camera_id: str, user=Depends(get_current_user)):
    stream = _streams.get(camera_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Camera not found or not running")
    snapshot = stream.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No frame available yet")
    return Response(content=snapshot, media_type="image/jpeg")


# ---------- ALERTS ----------

@app.get("/alerts")
def get_alerts(limit: int = 50, user=Depends(get_current_user)):
    conn = sqlite3.connect(_db_path)
    rows = conn.execute(
        """SELECT id, camera_id, alert_type, people_count, person_label,
                  timestamp, snapshot_path
           FROM alerts ORDER BY id DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return JSONResponse(content={"alerts": [
        {
            "id": r[0], "camera_id": r[1], "alert_type": r[2],
            "people_count": r[3], "person_label": r[4],
            "timestamp": r[5], "snapshot_path": r[6]
        } for r in rows
    ]})


@app.get("/count/{camera_id}")
def get_count(camera_id: str, user=Depends(get_current_user)):
    data = _results.get(camera_id, {})
    count = data.get("people_counter", {}).get("people_count", 0)
    return {"camera_id": camera_id, "people_count": count}


# ---------- CONFIG ----------

@app.get("/config")
def get_config(user=Depends(get_current_user)):
    return _load_config()


class ROIUpdate(BaseModel):
    camera_id: str
    roi_index: Optional[int] = 0   # which ROI to update
    points: List[List[int]]        # [[x,y], [x,y], ...] polygon points


class ROIDelete(BaseModel):
    camera_id: str
    roi_index: int


class ModuleUpdate(BaseModel):
    camera_id: str
    modules: dict


class CameraSourceUpdate(BaseModel):
    camera_id: str
    source: str


@app.post("/config/roi")
def update_roi(body: ROIUpdate, user=Depends(require_admin)):
    config = _load_config()
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            # Support multiple ROIs as a list of polygon point lists
            if "intrusion_roi" not in cam:
                cam["intrusion_roi"] = []
            # Update existing or append new
            if not isinstance(cam.get("intrusion_roi"), list):
                cam["intrusion_roi"] = []
            if body.roi_index < len(cam["intrusion_roi"]):
                cam["intrusion_roi"][body.roi_index] = body.points
            else:
                cam["intrusion_roi"].append(body.points)
            # Also keep flat roi for backward compat (bounding box of first ROI)
            if cam["intrusion_roi"]:
                pts = cam["intrusion_roi"][0]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                cam["intrusion_roi"] = [min(xs), min(ys), max(xs), max(ys)]
            break
    _save_config(config)

    # Hot-reload in running pipeline
    pipeline = _pipelines.get(body.camera_id)
    if pipeline:
        flat_roi = cam.get("intrusion_roi")
        if flat_roi:
            pipeline.update_roi(flat_roi)

    return {"message": "ROI updated and applied in runtime."}


@app.delete("/config/roi")
def delete_roi(body: ROIDelete, user=Depends(require_admin)):
    config = _load_config()
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            rois = cam.get("intrusion_roi", [])
            if body.roi_index < len(rois):
                rois.pop(body.roi_index)
            cam["intrusion_roi"] = rois
            if rois:
                pts = rois[0]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                cam["intrusion_roi"] = [min(xs), min(ys), max(xs), max(ys)]
            else:
                cam["intrusion_roi"] = None
            break
    _save_config(config)

    pipeline = _pipelines.get(body.camera_id)
    if pipeline and cam.get("intrusion_roi"):
        pipeline.update_roi(cam["intrusion_roi"])

    return {"message": "ROI deleted."}


@app.post("/config/modules")
def update_modules(body: ModuleUpdate, user=Depends(require_admin)):
    config = _load_config()
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            cam["modules"].update(body.modules)
            break
    _save_config(config)

    # Hot-reload in running pipeline
    pipeline = _pipelines.get(body.camera_id)
    if pipeline:
        pipeline.update_modules(body.modules)

    return {"message": "Modules updated and applied in runtime."}


@app.post("/config/source")
def update_source(body: CameraSourceUpdate, user=Depends(require_admin)):
    config = _load_config()
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            cam["source"] = body.source
            break
    _save_config(config)
    return {"message": "Source updated. Restart backend to apply to this camera."}


# ---------- USERS ----------

@app.get("/users")
def list_users(user=Depends(require_admin)):
    return {"users": get_all_users(_auth_db)}


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"


@app.post("/users")
def add_user(body: UserCreate, user=Depends(require_admin)):
    success = create_user(body.username, body.password, body.role, _auth_db)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": f"User {body.username} created"}


@app.delete("/users/{username}")
def remove_user(username: str, user=Depends(require_admin)):
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete default admin")
    delete_user(username, _auth_db)
    return {"message": f"User {username} deleted"}