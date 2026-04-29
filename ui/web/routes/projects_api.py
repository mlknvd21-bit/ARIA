import os
import socket
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flask import Blueprint, jsonify

projects_bp = Blueprint('projects', __name__)

PROJECTS_DIR = os.path.join(os.path.expanduser("~"), "aria_projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Track running servers: project_name -> (port, server_object)
running_servers = {}

def find_free_port():
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def serve_project(project_name, project_path, port):
    """Start an HTTP server for the project directory in a background thread."""
    original_cwd = os.getcwd()
    try:
        os.chdir(project_path)
        handler = SimpleHTTPRequestHandler
        httpd = HTTPServer(('127.0.0.1', port), handler)  # only localhost for safety
        running_servers[project_name] = (port, httpd)
        print(f"[Project Server] Serving '{project_name}' on http://127.0.0.1:{port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"[Project Server] Error: {e}")
    finally:
        os.chdir(original_cwd)
        if project_name in running_servers:
            # Only remove if this is the same server (avoid race)
            if running_servers[project_name][1] is httpd:
                del running_servers[project_name]

@projects_bp.route('/api/projects', methods=['GET'])
def list_projects():
    try:
        items = os.listdir(PROJECTS_DIR)
        projects = []
        for name in items:
            full_path = os.path.join(PROJECTS_DIR, name)
            if os.path.isdir(full_path):
                has_web = os.path.isfile(os.path.join(full_path, 'index.html'))
                already_running = name in running_servers
                projects.append({
                    "name": name,
                    "has_web": has_web,
                    "running": already_running,
                    "port": running_servers[name][0] if already_running else None
                })
        return jsonify(projects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/api/projects/<name>/files', methods=['GET'])
def project_files(name):
    full_path = os.path.join(PROJECTS_DIR, name)
    if not os.path.isdir(full_path):
        return jsonify({"error": "Project not found"}), 404
    try:
        files = []
        for f in sorted(os.listdir(full_path)):
            fp = os.path.join(full_path, f)
            files.append({
                "name": f,
                "type": "file" if os.path.isfile(fp) else "dir"
            })
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/api/projects/<name>/run', methods=['POST'])
def run_project(name):
    full_path = os.path.join(PROJECTS_DIR, name)
    if not os.path.isdir(full_path):
        return jsonify({"error": "Project not found"}), 404

    # If already running, return existing port
    if name in running_servers:
        port = running_servers[name][0]
        return jsonify({"port": port, "url": f"http://127.0.0.1:{port}", "already_running": True})

    # Start a new server
    port = find_free_port()
    thread = threading.Thread(
        target=serve_project,
        args=(name, full_path, port),
        daemon=True
    )
    thread.start()
    time.sleep(0.5)  # Wait for server to start
    return jsonify({"port": port, "url": f"http://127.0.0.1:{port}", "already_running": False})

@projects_bp.route('/api/projects/<name>/stop', methods=['POST'])
def stop_project(name):
    if name not in running_servers:
        return jsonify({"error": "Project not running"}), 404
    port, httpd = running_servers[name]
    httpd.shutdown()
    del running_servers[name]
    return jsonify({"stopped": name, "port": port})
