import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Flask, render_template
from config.loader import Config
from core.history import ConversationHistory
from core.memory import SemanticMemory
from core.engine import Engine
from core.swarm import Swarm
from providers.manager import ProviderManager
from ui.web.routes.chat_api import chat_bp
from ui.web.routes.settings_api import settings_bp
from ui.web.routes.projects_api import projects_bp
from ui.web.routes.swarm_api import swarm_bp, swarm_instance
from ui.web.routes.bug_api import bug_bp
from ui.web.routes.android_api import android_bp
from ui.web.routes.plugin_api import plugin_bp

app = Flask(__name__)
app.register_blueprint(chat_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(swarm_bp)
app.register_blueprint(bug_bp)
app.register_blueprint(android_bp)
app.register_blueprint(plugin_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quran')
def quran_app():
    return app.send_static_file('quran.html')

@app.route('/quran_data/<path:filename>')
def quran_data(filename):
    import os
    return app.send_static_file(os.path.join('quran_data', filename))

def create_web_app():
    print("Loading configuration...")
    config = Config()
    
    print("Initializing Provider Manager...")
    manager = ProviderManager()
    provider = manager.get_active_provider()
    print(f"Active provider: {manager.priority_order[0] if manager.priority_order else 'unknown'}")
    
    print("Initializing Memory...")
    memory = SemanticMemory()
    
    print("Initializing History and Engine...")
    history = ConversationHistory()
    engine = Engine(provider, history, memory, manager)
    
    import ui.web.routes.chat_api as chat_mod
    chat_mod.engine = engine
    chat_mod.history = history
    
    import ui.web.routes.settings_api as settings_mod
    settings_mod.manager = manager
    settings_mod.memory = memory
    
    print("Initializing Swarm...")
    swarm = Swarm(manager, memory)
    import ui.web.routes.swarm_api as swarm_mod
    swarm_mod.swarm_instance = swarm
    
    print("ARIA Web GUI ready with Plugin Manager.")
    return app, manager, memory

if __name__ == '__main__':
    app, _, _ = create_web_app()
    print("Starting ARIA Web GUI on http://0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000, debug=False)
