from flask import request, jsonify
from api import ai_chat_bp
from groq import Groq
from config import Config

client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None

@ai_chat_bp.route('/generate_warning', methods=['GET'])
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

@ai_chat_bp.route('/chat', methods=['POST'])
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
