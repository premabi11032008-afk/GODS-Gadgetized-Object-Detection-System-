from flask import request, jsonify, session
from api import auth_bp

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Basic hardcoded check
    if username == 'admin' and password == 'password':
        session['logged_in'] = True
        return jsonify({"success": True, "message": "Logged in successfully"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@auth_bp.route('/status', methods=['GET'])
def status():
    return jsonify({"logged_in": session.get('logged_in', False)})
