import json, subprocess, os, re
from flask import Blueprint, jsonify, request

android_bp = Blueprint('android', __name__)

# (existing endpoints unchanged, we'll just add the new two)
@android_bp.route('/api/android/battery', methods=['GET'])
def battery():
    try:
        result = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout:
            return jsonify(json.loads(result.stdout))
        return jsonify({"error": "Battery command failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/sms', methods=['POST'])
def sms():
    data = request.get_json()
    number = data.get('number','').strip()
    text = data.get('text','').strip()
    if not number or not text:
        return jsonify({"error": "Number and text required"}), 400
    try:
        result = subprocess.run(["termux-sms-send","-n",number,text], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return jsonify({"success": True, "message": "SMS sent"})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/notify', methods=['POST'])
def notify():
    data = request.get_json()
    title = data.get('title','ARIA')
    body = data.get('body','')
    if not body:
        return jsonify({"error": "Body required"}), 400
    try:
        result = subprocess.run(["termux-notification","-t",title,"-c",body], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return jsonify({"success": True, "message": "Notification sent"})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/camera', methods=['POST'])
def camera():
    try:
        save_dir = os.path.expanduser("~/storage/pictures")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "aria_photo.jpg")
        result = subprocess.run(["termux-camera-photo", save_path], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            subprocess.run(["termux-media-scan", save_path], capture_output=True, text=True, timeout=10)
            return jsonify({"success": True, "path": save_path})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/wifi_scan', methods=['GET'])
def wifi_scan():
    try:
        result = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout:
            return jsonify(json.loads(result.stdout)[:10])
        return jsonify({"error": "Scan failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/wifi_connection', methods=['GET'])
def wifi_connection():
    try:
        result = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=8)
        if result.returncode == 0 and result.stdout:
            return jsonify(json.loads(result.stdout))
        return jsonify({"error": "Connection info failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/media', methods=['POST'])
def media():
    data = request.get_json()
    command = data.get('command','').strip().lower()
    if command not in ['play','pause','stop','next','prev','info']:
        return jsonify({"error": "Invalid command"}), 400
    try:
        result = subprocess.run(["termux-media-player", command], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return jsonify({"success": True, "result": result.stdout.strip()})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/sms_inbox', methods=['GET'])
def sms_inbox():
    try:
        result = subprocess.run(["termux-sms-list"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout:
            return jsonify(json.loads(result.stdout)[:5])
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/alarm', methods=['POST'])
def alarm():
    data = request.get_json()
    time_ms = data.get('time_ms','')
    title = data.get('title','ARIA Alarm')
    if not time_ms:
        return jsonify({"error": "time_ms required"}), 400
    try:
        result = subprocess.run(["termux-alarm","-t",time_ms,"-n",title], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return jsonify({"success": True})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/schedule_notify', methods=['POST'])
def schedule_notify():
    data = request.get_json()
    time_str = data.get('time','')
    message = data.get('message','')
    if not time_str or not message:
        return jsonify({"error": "time (HH:MM) and message required"}), 400
    if not re.match(r"^\d{1,2}:\d{2}$", time_str):
        return jsonify({"error": "Time format must be HH:MM (24-hour)"}), 400
    try:
        full_cmd = f'echo termux-notification -c "{message}" | at {time_str}'
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return jsonify({"success": True, "scheduled": time_str})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/location', methods=['GET'])
def location():
    try:
        result = subprocess.run(["termux-location"], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout:
            return jsonify(json.loads(result.stdout))
        return jsonify({"error": "Location failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----- NEW: Speech and TTS endpoints -----
@android_bp.route('/api/android/speech_to_text', methods=['POST'])
def speech_to_text():
    data = request.get_json()
    lang = data.get('lang','en').strip()
    try:
        cmd = ["termux-speech-to-text"]
        if lang:
            cmd.extend(["-l", lang])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode == 0 and result.stdout:
            return jsonify({"text": result.stdout.strip()})
        return jsonify({"error": "No speech recognized"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@android_bp.route('/api/android/text_to_speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text','').strip()
    lang = data.get('lang','en').strip()
    if not text:
        return jsonify({"error": "text required"}), 400
    try:
        cmd = ["termux-tts-speak"]
        if lang:
            cmd.extend(["-l", lang])
        cmd.append(text)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return jsonify({"success": True})
        return jsonify({"error": result.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
