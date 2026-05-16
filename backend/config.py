import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Camera and Streaming Configurations
    CAMERA_SOURCE = 0
    TARGET_FPS = 10
    DETECTION_INTERVAL = 1 
    FRAME_SIZE = (320, 320)
    JPEG_QUALITY = 90

    # Driving Safety Globals
    # We use thread-safe ways to access these in a real app, but for now they live here.
    camera_rotation = 0
