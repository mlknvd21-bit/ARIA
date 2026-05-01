import os, re, json
from flask import Blueprint, jsonify

bug_bp = Blueprint('bug', __name__)

LOG_FILE = os.path.expanduser("~/aria/logs/aria_server.log")

# -------------------- Static Code Scan --------------------
@bug_bp.route('/api/bugs/scan', methods=['GET'])
def scan_static():
    from tools.bug_detector import BugDetectorTool
    tool = BugDetectorTool()
    result = tool.execute({"action": "scan"})
    return jsonify({"result": result})

# -------------------- Runtime Errors (existing) --------------------
@bug_bp.route('/api/bugs/runtime', methods=['GET'])
def scan_runtime():
    if not os.path.isfile(LOG_FILE):
        return jsonify({"result": "ℹ️ No log file found. Use 'arwl' to start ARIA with logging."})
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    recent = lines[-500:]
    errors = []
    for line in recent:
        m = re.search(r'" (\d{3})', line)
        if m and int(m.group(1)) >= 400:
            errors.append({"status": int(m.group(1)), "raw": line.strip()})
    if not errors:
        return jsonify({"result": "✅ No runtime errors (4xx/5xx) in recent logs."})
    report = f"🔍 Found {len(errors)} runtime error(s):\n"
    for i, e in enumerate(errors, 1):
        report += f"--- Error {i} ---\nStatus: {e['status']}\nLine: {e['raw']}\n\n"
    return jsonify({"result": report})

# -------------------- Missing Files (404) --------------------
@bug_bp.route('/api/bugs/missing-files', methods=['GET'])
def scan_missing():
    if not os.path.isfile(LOG_FILE):
        return jsonify({"result": "ℹ️ No log file found. Use 'arwl' to start ARIA with logging."})
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    missing = {}
    for line in lines:
        if ' 404 ' in line:
            m = re.search(r'GET (\S+)', line)
            if m:
                path = m.group(1)
                missing[path] = missing.get(path, 0) + 1
    if not missing:
        return jsonify({"result": "✅ No missing files (404) in recent logs."})
    report = f"🔍 Found {len(missing)} unique missing file(s):\n"
    sorted_missing = sorted(missing.items(), key=lambda x: x[1], reverse=True)
    for i, (path, count) in enumerate(sorted_missing, 1):
        report += f"--- File {i} ---\nPath: {path}\nOccurrences: {count}\n\n"
    return jsonify({"result": report})

# -------------------- Status Summary --------------------
@bug_bp.route('/api/bugs/status-summary', methods=['GET'])
def scan_status_summary():
    if not os.path.isfile(LOG_FILE):
        return jsonify({"result": "ℹ️ No log file found. Use 'arwl' to start ARIA with logging."})
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    counts = {"200": 0, "304": 0, "404": 0, "500": 0, "other": 0}
    for line in lines:
        m = re.search(r'" (\d{3})', line)
        if m:
            code = m.group(1)
            if code in counts:
                counts[code] += 1
            else:
                counts["other"] += 1
    total = sum(counts.values())
    report = f"📊 Server Status Summary (Total Requests: {total})\n"
    report += f"🟢 200 OK: {counts['200']}\n"
    report += f"🔵 304 Not Modified: {counts['304']}\n"
    report += f"🟡 404 Not Found: {counts['404']}\n"
    report += f"🔴 500 Server Error: {counts['500']}\n"
    if counts['other'] > 0:
        report += f"⚪ Other: {counts['other']}\n"
    return jsonify({"result": report})
