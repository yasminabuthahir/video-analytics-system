import sqlite3
import json
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
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
_pipelines = {}


def init_api(db_path: str, pipelines_ref: dict):
    global _db_path, _pipelines
    _db_path = db_path
    _pipelines = pipelines_ref
    init_auth_db(_auth_db)
    # Serve media folder for snapshots
    if os.path.exists("media"):
        app.mount("/media", StaticFiles(directory="media"), name="media")


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
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
        for cam_id, data in _pipelines.items()
    ]}


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
    data = _pipelines.get(camera_id, {})
    count = data.get("people_counter", {}).get("people_count", 0)
    return {"camera_id": camera_id, "people_count": count}


# ---------- CONFIG ----------

@app.get("/config")
def get_config(user=Depends(get_current_user)):
    with open(_config_path) as f:
        return json.load(f)


class ROIUpdate(BaseModel):
    camera_id: str
    roi: list


class ModuleUpdate(BaseModel):
    camera_id: str
    modules: dict


class CameraSourceUpdate(BaseModel):
    camera_id: str
    source: str


@app.post("/config/roi")
def update_roi(body: ROIUpdate, user=Depends(require_admin)):
    with open(_config_path) as f:
        config = json.load(f)
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            cam["intrusion_roi"] = body.roi
            break
    with open(_config_path, "w") as f:
        json.dump(config, f, indent=2)
    return {"message": "ROI updated. Restart pipeline to apply."}


@app.post("/config/modules")
def update_modules(body: ModuleUpdate, user=Depends(require_admin)):
    with open(_config_path) as f:
        config = json.load(f)
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            cam["modules"].update(body.modules)
            break
    with open(_config_path, "w") as f:
        json.dump(config, f, indent=2)
    return {"message": "Modules updated. Restart pipeline to apply."}


@app.post("/config/source")
def update_source(body: CameraSourceUpdate, user=Depends(require_admin)):
    with open(_config_path) as f:
        config = json.load(f)
    for cam in config["cameras"]:
        if cam["camera_id"] == body.camera_id:
            cam["source"] = body.source
            break
    with open(_config_path, "w") as f:
        json.dump(config, f, indent=2)
    return {"message": "Source updated. Restart pipeline to apply."}


# ---------- USERS (admin only) ----------

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