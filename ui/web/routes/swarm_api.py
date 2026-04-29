from flask import Blueprint, request, jsonify

swarm_bp = Blueprint('swarm', __name__)

# These will be set by server.py
swarm_instance = None

@swarm_bp.route('/api/swarm', methods=['POST'])
def run_swarm():
    if swarm_instance is None:
        return jsonify({"error": "Swarm module not initialized"}), 500
    data = request.get_json()
    task = data.get('task', '').strip()
    if not task:
        return jsonify({"error": "No task provided"}), 400
    try:
        result = swarm_instance.run(task)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
