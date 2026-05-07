import sqlite3
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Video Analytics System")

_db_path = None
_pipelines = {}  # camera_id -> latest results


def init_api(db_path: str, pipelines_ref: dict):
    global _db_path, _pipelines
    _db_path = db_path
    _pipelines = pipelines_ref


@app.get("/")
def root():
    return {"message": "Video Analytics System running"}


@app.get("/status")
def get_status():
    return {
        "cameras": [
            {"camera_id": cam_id, "latest": data}
            for cam_id, data in _pipelines.items()
        ]
    }


@app.get("/alerts")
def get_alerts(limit: int = 50):
    conn = sqlite3.connect(_db_path)
    rows = conn.execute(
        "SELECT camera_id, alert_type, data, timestamp FROM alerts ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    alerts = [
        {
            "camera_id": r[0],
            "alert_type": r[1],
            "data": json.loads(r[2]),
            "timestamp": r[3]
        }
        for r in rows
    ]
    return JSONResponse(content={"alerts": alerts})


@app.get("/count/{camera_id}")
def get_count(camera_id: str):
    data = _pipelines.get(camera_id, {})
    count = data.get("people_counter", {}).get("people_count", 0)
    return {"camera_id": camera_id, "people_count": count}