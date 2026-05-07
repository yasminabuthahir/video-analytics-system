import json
import threading
import uvicorn
from app.camera_manager import CameraStream
from app.pipeline import Pipeline
from app.api import app, init_api


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def run_camera(cam_config, face_config, db_path, results_store):
    stream = CameraStream(cam_config["camera_id"], cam_config["source"])
    if not stream.start():
        return

    pipeline = Pipeline(cam_config, face_config, db_path)

    import cv2
    while True:
        frame = stream.get_frame()
        if frame is None:
            continue

        processed_frame, summary = pipeline.process_frame(frame)
        results_store[cam_config["camera_id"]] = summary

        cv2.imshow(cam_config["name"], processed_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stream.stop()
            break

    cv2.destroyAllWindows()


def main():
    config = load_config()
    db_path = config["output"]["alerts_db"]
    face_config = config["face_recognition"]
    results_store = {}

    init_api(db_path, results_store)

    # Start each camera in its own thread
    threads = []
    for cam in config["cameras"]:
        if cam.get("enabled", True):
            t = threading.Thread(
                target=run_camera,
                args=(cam, face_config, db_path, results_store),
                daemon=True
            )
            t.start()
            threads.append(t)

    # Start FastAPI server (blocking)
    uvicorn.run(app, host=config["server"]["host"], port=config["server"]["port"])


if __name__ == "__main__":
    main()