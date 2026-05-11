import os
from flask import Flask, request, jsonify, Response, session
from flask_cors import CORS
import cv2
import threading
import time
from dotenv import load_dotenv
from groq import Groq
from driving_safety import detect_objects, draw_detections, detect_lanes, check_hazards

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-me")

# Required for cross-domain cookies (Vercel frontend -> Backend)
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

# Allow requests from frontend and allow credentials (cookies)
CORS(app, supports_credentials=True)

# Configure Groq API client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

global_hazard_state = {
    "hazard": False,
    "distance": None,
    "risk_score": 0,
    "latest_log": "System initialized. Awaiting feed..."
}
camera_rotation = 0
lock = threading.Lock()
CAMERA_SOURCE = 0

# Shared state
latest_detections = None
latest_lane = None
latest_metadata = {}
frame_lock = threading.Lock()

# Performance configs
TARGET_FPS = 10
DETECTION_INTERVAL = 1 
FRAME_SIZE = (320, 320)
JPEG_QUALITY = 50

frame_count = 0


def generate_frames():
    global latest_detections, latest_lane, latest_metadata, frame_count, global_hazard_state

    last_time = 0
    camera = cv2.VideoCapture(CAMERA_SOURCE)

    if not camera.isOpened():
        global_hazard_state = {
            "hazard": False,
            "distance": None,
            "risk_score": 0,
            "latest_log": f"Failed to open camera source: {CAMERA_SOURCE}"
        }
        return

    while True:
        current_time = time.time()
        if current_time - last_time < 1 / TARGET_FPS:
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
        if camera_rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif camera_rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif camera_rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)


        frame_count += 1

        # 🧠 Run heavy detection only every N frames
        if frame_count % DETECTION_INTERVAL == 0:
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
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        )
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Basic hardcoded check
    if username == 'admin' and password == 'password':
        session['logged_in'] = True
        return jsonify({"success": True, "message": "Logged in successfully"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"logged_in": session.get('logged_in', False)})

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    # Optional: check if logged in before streaming (simple check via query param or cookie)
    # Since it's accessed via <img>, cookies are sent automatically if we configure CORS correctly
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/hazard', methods=['GET'])
def hazard():
    global global_hazard_state
    return jsonify(global_hazard_state)



@app.route('/api/rotate', methods=['POST'])
def rotate_camera():
    global camera_rotation
    camera_rotation = (camera_rotation + 90) % 360
    return jsonify({"success": True, "rotation": camera_rotation})

@app.route('/api/generate_warning', methods=['GET'])
def generate_warning():
    if not client:
        return jsonify({"success": False, "message": "API Key not configured."}), 500
    try:
        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[{"role": "user", "content": "Generate a short, urgent 1-sentence warning message for a driver because an object is dangerously close to their vehicle."}],
            max_tokens=50
        )
        return jsonify({"success": True, "warning": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"success": False, "message": "API Key not configured."}), 500
        
    data = request.get_json()
    user_message = data.get('message', '')
    history = data.get('history', [])
    
    try:
        messages = [{"role": "system", "content": "You are an AI assistant for the SafeDrive AI platform. Be helpful, concise, and guide the user through the platform features (which includes a dashboard that monitors driving safety using computer vision)."}]
        
        # Append history
        for msg in history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            
        # Append the new message
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=messages,
            max_tokens=300
        )
        return jsonify({"success": True, "response": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
