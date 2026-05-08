import json
import threading
import signal
import sys
import time
import uvicorn
import cv2
from app.camera_manager import CameraStream
from app.pipeline import Pipeline
from app.api import app, init_api

stop_event = threading.Event()
streams_ref = {}
pipelines_ref = {}
results_ref = {}
frames_ref = {}   # camera_id -> latest processed frame
frames_lock = threading.Lock()


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def run_camera(cam_config, face_config, db_path):
    cam_id = cam_config["camera_id"]
    stream = CameraStream(cam_id, cam_config["source"])
    if not stream.start():
        return

    streams_ref[cam_id] = stream
    pipeline = Pipeline(cam_config, face_config, db_path)
    pipelines_ref[cam_id] = pipeline

    while not stop_event.is_set():
        frame = stream.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue

        processed_frame, summary = pipeline.process_frame(frame)
        results_ref[cam_id] = summary

        with frames_lock:
            frames_ref[cam_id] = processed_frame.copy()

    stream.stop()


def display_loop(camera_names: dict):
    """
    Single display thread — all cv2.imshow calls here.
    camera_names: {camera_id: window_name}
    """
    while not stop_event.is_set():
        with frames_lock:
            snapshot = {k: v.copy() for k, v in frames_ref.items() if v is not None}

        for cam_id, frame in snapshot.items():
            window_name = camera_names.get(cam_id, cam_id)
            cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            stop_event.set()
            break

        time.sleep(0.01)

    cv2.destroyAllWindows()


def shutdown(sig, frame):
    print("\n[Main] Shutting down cleanly...")
    stop_event.set()
    for s in streams_ref.values():
        s.stop()
    cv2.destroyAllWindows()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    config = load_config()
    db_path = config["output"]["alerts_db"]
    face_config = config["face_recognition"]

    init_api(db_path, pipelines_ref, streams_ref, results_ref)

    camera_names = {}
    threads = []

    for cam in config["cameras"]:
        if not cam.get("enabled", True):
            continue
        camera_names[cam["camera_id"]] = cam.get("name", cam["camera_id"])
        t = threading.Thread(
            target=run_camera,
            args=(cam, face_config, db_path),
            daemon=True
        )
        t.start()
        threads.append(t)

    # Give streams a moment to get first frames
    time.sleep(2)

    # Display loop runs on main thread — required for Qt/OpenCV on Linux
    display_thread = threading.Thread(
        target=display_loop,
        args=(camera_names,),
        daemon=True
    )
    display_thread.start()

    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"]
    )


if __name__ == "__main__":
    main()