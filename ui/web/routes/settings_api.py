from flask import Blueprint, jsonify, request
from utils.backup import create_backup, list_backups, restore_backup, get_backup_diff
import os
import json

settings_bp = Blueprint('settings', __name__)

manager = None
memory = None

MODEL_DESC_FILE = os.path.join(os.path.expanduser("~"), "aria", "data", "model_descriptions.json")
BACKUP_DIR = os.path.join(os.path.expanduser("~"), "aria", "backups")

# ---------- Providers ----------
@settings_bp.route('/api/providers', methods=['GET'])
def list_providers():
    if not manager:
        return jsonify({"error": "Provider manager not available"}), 500
    try:
        import yaml
        with open(manager.providers_config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        providers = config.get("providers", {})
        result = []
        for name, cfg in providers.items():
            enabled = cfg.get("enabled", True)
            priority = cfg.get("priority", "?")
            model = cfg.get("model", "?")
            api_env = cfg.get("api_key_env", "?")
            ptype = cfg.get("type", "?")
            active = (enabled and manager.priority_order and manager.priority_order[0] == name)
            result.append({
                "name": name, "type": ptype, "enabled": enabled,
                "active": active, "priority": priority,
                "model": model, "api_key_env": api_env
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- Models ----------
@settings_bp.route('/api/models', methods=['GET'])
def list_models():
    if not manager:
        return jsonify({"error": "Provider manager not available"}), 500
    try:
        model_ids = manager.get_available_models()
        desc = {}
        if os.path.isfile(MODEL_DESC_FILE):
            with open(MODEL_DESC_FILE, 'r') as f:
                desc = json.load(f)
        result = []
        for mid in model_ids:
            result.append({
                "id": mid,
                "description": desc.get(mid, "A powerful language model for general use.")
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/models/select', methods=['POST'])
def select_model():
    if not manager:
        return jsonify({"error": "Manager not available"}), 500
    req = request.get_json()
    model_id = req.get("model_id", "").strip()
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    ok, msg = manager.set_active_model(model_id)
    if ok:
        return jsonify({"success": True, "message": msg})
    return jsonify({"error": msg}), 400

# ---------- Memory ----------
@settings_bp.route('/api/memory', methods=['GET'])
def list_memory():
    if memory is None:
        return jsonify({"error": "Memory object is not initialized"}), 500
    try:
        keys = memory.all_keys()
        result = {}
        for key in keys:
            val = memory.recall(key)
            result[key] = val if val is not None else "(empty)"
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Memory error: {str(e)}"}), 500

@settings_bp.route('/api/memory/<key>', methods=['DELETE'])
def delete_memory(key):
    if memory is None:
        return jsonify({"error": "Memory not available"}), 500
    try:
        memory.forget(key)
        return jsonify({"deleted": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- Backup ----------
@settings_bp.route('/api/backup', methods=['POST'])
def do_backup():
    data = request.get_json() or {}
    custom_name = data.get('custom_name', '').strip() or None
    try:
        filename, diff = create_backup(custom_name)
        return jsonify({"success": True, "filename": filename, "diff": diff})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/backups', methods=['GET'])
def do_list_backups():
    try:
        files = list_backups()
        result = []
        for f in files:
            filepath = os.path.join(BACKUP_DIR, f)
            try:
                stat = os.stat(filepath)
                size_kb = round(stat.st_size / 1024, 1)
                import datetime
                date_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                size_kb = 0; date_str = "Unknown"
            result.append({"name": f, "size_kb": size_kb, "date": date_str})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/backup_diff/<filename>', methods=['GET'])
def do_backup_diff(filename):
    try:
        diff = get_backup_diff(filename)
        return jsonify({"diff": diff})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/backup/rename', methods=['POST'])
def rename_backup():
    data = request.get_json() or {}
    old_name = data.get('old_name', '').strip()
    new_name = data.get('new_name', '').strip()
    if not old_name or not new_name:
        return jsonify({"error": "old_name and new_name required"}), 400
    old_path = os.path.join(BACKUP_DIR, old_name)
    if not os.path.isfile(old_path):
        return jsonify({"error": "File not found"}), 404
    safe_new = "".join(c if c.isalnum() or c in "._-" else "_" for c in new_name)
    if not safe_new.endswith(".tar.gz"):
        safe_new += ".tar.gz"
    new_path = os.path.join(BACKUP_DIR, safe_new)
    if os.path.exists(new_path):
        return jsonify({"error": "A backup with that name already exists"}), 409
    try:
        os.rename(old_path, new_path)
        old_manifest = old_path.replace(".tar.gz", ".json")
        new_manifest = new_path.replace(".tar.gz", ".json")
        if os.path.isfile(old_manifest):
            os.rename(old_manifest, new_manifest)
        return jsonify({"success": True, "new_name": safe_new})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/restore', methods=['POST'])
def do_restore():
    data = request.get_json() or {}
    filename = data.get("filename", "").strip()
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    try:
        restore_backup(filename)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/backup/<filename>', methods=['DELETE'])
def delete_backup(filename):
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404
    try:
        os.remove(filepath)
        manifest_path = filepath.replace(".tar.gz", ".json")
        if os.path.isfile(manifest_path):
            os.remove(manifest_path)
        return jsonify({"success": True, "deleted": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
