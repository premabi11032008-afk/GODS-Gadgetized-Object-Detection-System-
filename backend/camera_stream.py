import cv2
import time
import threading
from config import Config
from vision.object_detection import detect_objects, draw_detections
from vision.lane_detection import detect_lanes
from vision.hazard_logic import check_hazards

# Shared state
global_hazard_state = {
    "hazard": False,
    "distance": None,
    "risk_score": 0,
    "latest_log": "System initialized. Awaiting feed..."
}
latest_detections = None
latest_lane = None
latest_metadata = {}
frame_lock = threading.Lock()
frame_count = 0

def get_hazard_state():
    return global_hazard_state

def get_camera_rotation():
    return Config.camera_rotation

def set_camera_rotation(rotation):
    Config.camera_rotation = rotation

def generate_frames():
    global latest_detections, latest_lane, latest_metadata, frame_count, global_hazard_state

    last_time = 0
    camera = cv2.VideoCapture(Config.CAMERA_SOURCE)

    if not camera.isOpened():
        global_hazard_state = {
            "hazard": False,
            "distance": None,
            "risk_score": 0,
            "latest_log": f"Failed to open camera source: {Config.CAMERA_SOURCE}"
        }
        return

    while True:
        current_time = time.time()
        if current_time - last_time < 1 / Config.TARGET_FPS:
            continue
        last_time = current_time

        success, frame = camera.read()
        if not success or frame is None:
            with frame_lock:
                global_hazard_state = {
                    "hazard": False,
                    "distance": None,
                    "risk_score": 0,
                    "latest_log": "Camera opened, but no frame could be read."
                }
            time.sleep(0.2)
            continue

        # 🔄 Rotate if needed
        rotation = Config.camera_rotation
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        frame_count += 1

        # 🧠 Run heavy detection only every N frames
        if frame_count % Config.DETECTION_INTERVAL == 0:
            detections = detect_objects(frame)
            frame, lane_detected = detect_lanes(frame)
            frame, hazard, metadata = check_hazards(frame, detections, lane_detected)

            # Cache results
            with frame_lock:
                latest_detections = detections
                latest_lane = lane_detected
                latest_metadata = metadata

                global_hazard_state = {
                    "hazard": hazard,
                    "distance": metadata.get("distance"),
                    "risk_score": metadata.get("risk_score"),
                    "latest_log": metadata.get("log")
                }

        else:
            # 🧩 Use cached results (fast path)
            with frame_lock:
                if latest_detections is not None:
                    frame = draw_detections(frame, latest_detections)

        # 🖼 Encode with lower quality
        ret, buffer = cv2.imencode(
            '.jpg', frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), Config.JPEG_QUALITY]
        )
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')
