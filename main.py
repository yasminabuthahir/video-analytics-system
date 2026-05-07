import json
import threading
import signal
import sys
import uvicorn
import cv2
from app.camera_manager import CameraStream
from app.pipeline import Pipeline
from app.api import app, init_api

streams = []
stop_event = threading.Event()


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def run_camera(cam_config, face_config, db_path, results_store, stop_event):
    stream = CameraStream(cam_config["camera_id"], cam_config["source"])
    if not stream.start():
        return
    streams.append(stream)

    pipeline = Pipeline(cam_config, face_config, db_path)

    while not stop_event.is_set():
        frame = stream.get_frame()
        if frame is None:
            continue
        processed_frame, summary = pipeline.process_frame(frame)
        results_store[cam_config["camera_id"]] = summary
        cv2.imshow(cam_config["name"], processed_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_event.set()
            break

    stream.stop()
    cv2.destroyAllWindows()


def shutdown(sig, frame):
    print("\n[Main] Shutting down cleanly...")
    stop_event.set()
    for s in streams:
        s.stop()
    cv2.destroyAllWindows()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    config = load_config()
    db_path = config["output"]["alerts_db"]
    face_config = config["face_recognition"]
    results_store = {}

    init_api(db_path, results_store)

    for cam in config["cameras"]:
        if cam.get("enabled", True):
            t = threading.Thread(
                target=run_camera,
                args=(cam, face_config, db_path, results_store, stop_event),
                daemon=True
            )
            t.start()

    uvicorn.run(app, host=config["server"]["host"], port=config["server"]["port"])


if __name__ == "__main__":
    main()