from flask import Blueprint, jsonify, request
from plugins.manager import PluginManager
from plugins.loader import PluginLoader
from utils.logger import get_logger

logger = get_logger(__name__)
plugin_bp = Blueprint('plugin', __name__)

def get_manager():
    return PluginManager()

def get_loader():
    loader = PluginLoader()
    loader.discover_and_load()
    return loader

@plugin_bp.route('/api/plugins', methods=['GET'])
def list_plugins():
    manager = get_manager()
    plugins = manager.list_plugins()
    return jsonify(plugins)

@plugin_bp.route('/api/plugins/<name>/toggle', methods=['POST'])
def toggle_plugin(name):
    manager = get_manager()
    data = request.get_json()
    enabled = data.get('enabled', True)
    if manager.set_enabled(name, enabled):
        return jsonify({"success": True, "enabled": enabled})
    return jsonify({"error": "Plugin not found"}), 404

@plugin_bp.route('/api/plugins/<name>/info', methods=['GET'])
def plugin_info(name):
    manager = get_manager()
    info = manager.get_plugin_info(name)
    if info:
        return jsonify(info)
    return jsonify({"error": "Plugin not found"}), 404

# ========== NEW: Widgets Endpoint ==========
@plugin_bp.route('/api/plugins/widgets', methods=['GET'])
def plugin_widgets():
    """
    Return HTML widgets for all enabled plugins that have web_widgets defined.
    """
    manager = get_manager()
    loader = get_loader()
    widgets = []

    for plugin_name, manifest in loader.loaded_plugins.items():
        if not manager.is_enabled(plugin_name):
            continue

        widget_names = manifest.get("web_widgets", [])
        if not widget_names:
            continue

        # Look for instances that can provide widget HTML
        for widget_name in widget_names:
            # Find the tool instance for this plugin
            tool_name = manifest.get("tools", [None])[0]  # first tool
            if tool_name and tool_name in loader.extra_tools:
                tool = loader.extra_tools[tool_name]
                if hasattr(tool, 'get_widget_html'):
                    try:
                        html = tool.get_widget_html(widget_name)
                        widgets.append({
                            "plugin": plugin_name,
                            "widget_name": widget_name,
                            "html": html
                        })
                    except Exception as e:
                        logger.error(f"Error generating widget for {plugin_name}: {e}")

    return jsonify(widgets)
