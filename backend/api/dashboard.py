from flask import request, jsonify, Response
from api import dashboard_bp, video_bp
import camera_stream
import csv
import os
import time
import uuid

CSV_FILE = 'potholes.csv'

# Initialize CSV with headers if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'lat', 'lng', 'timestamp', 'status'])

@video_bp.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(camera_stream.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@dashboard_bp.route('/hazard', methods=['GET'])
def hazard():
    return jsonify(camera_stream.get_hazard_state())

@dashboard_bp.route('/rotate', methods=['POST'])
def rotate_camera():
    current_rot = camera_stream.get_camera_rotation()
    new_rot = (current_rot + 90) % 360
    camera_stream.set_camera_rotation(new_rot)
    return jsonify({"success": True, "rotation": new_rot})

@dashboard_bp.route('/potholes', methods=['GET'])
def get_potholes():
    potholes = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                potholes.append(row)
    return jsonify({"success": True, "potholes": potholes})

@dashboard_bp.route('/potholes', methods=['POST'])
def add_pothole():
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    
    if lat is None or lng is None:
        return jsonify({"success": False, "message": "Missing coordinates"}), 400
        
    new_pothole = {
        'id': str(uuid.uuid4()),
        'lat': lat,
        'lng': lng,
        'timestamp': int(time.time()),
        'status': 'detected'
    }
    
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([new_pothole['id'], new_pothole['lat'], new_pothole['lng'], new_pothole['timestamp'], new_pothole['status']])
        
    return jsonify({"success": True, "pothole": new_pothole})

@dashboard_bp.route('/potholes/<pothole_id>', methods=['DELETE'])
def delete_pothole(pothole_id):
    if not os.path.exists(CSV_FILE):
        return jsonify({"success": False, "message": "No data found"}), 404
        
    rows = []
    found = False
    with open(CSV_FILE, mode='r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows.append(headers)
        for row in reader:
            if row[0] == pothole_id:
                found = True
            else:
                rows.append(row)
                
    if found:
        with open(CSV_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return jsonify({"success": True, "message": "Pothole removed"})
    
    return jsonify({"success": False, "message": "Pothole not found"}), 404

