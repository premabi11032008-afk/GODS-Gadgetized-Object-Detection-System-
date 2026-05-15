import os
from flask import Flask
from flask_cors import CORS
from config import Config

# Import blueprints
from api.auth import auth_bp
from api.ai_chat import ai_chat_bp
from api.dashboard import dashboard_bp, video_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    # Required for cross-domain cookies
    app.config.update(
        SESSION_COOKIE_SAMESITE=Config.SESSION_COOKIE_SAMESITE,
        SESSION_COOKIE_SECURE=Config.SESSION_COOKIE_SECURE
    )

    # Allow requests from frontend and allow credentials
    CORS(app, supports_credentials=True)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(ai_chat_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(video_bp) # video_feed goes to root /video_feed

    return app

app = create_app()

if __name__ == '__main__':
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
