from flask import request, jsonify, Response
from api import dashboard_bp, video_bp
import camera_stream

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
