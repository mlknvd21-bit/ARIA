from flask import Blueprint, request, jsonify

chat_bp = Blueprint('chat', __name__)

# Global references — will be set by server.py
engine = None
history = None

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if engine is None:
        return jsonify({"error": "Engine not initialized"}), 500

    # Use the same engine.process() as CLI
    response = engine.process(user_message)
    return jsonify({"response": response})
