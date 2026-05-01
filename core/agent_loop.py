from typing import Dict
from tools.shell import ShellTool
from tools.filesystem import FileSystemTool
from tools.package_manager import PackageManagerTool
from tools.memory import MemoryTool
from tools.termux_api import TermuxAPITool
from tools.web_search import WebSearchTool
from tools.bug_detector import BugDetectorTool
from core.history import ConversationHistory
from core.memory import SemanticMemory
from plugins.loader import PluginLoader
from plugins.manager import PluginManager
from utils.logger import get_logger

logger = get_logger(__name__)

class AgentLoop:
    def __init__(self, provider, history: ConversationHistory, memory: SemanticMemory = None, provider_manager=None):
        self.provider = provider
        self.history = history
        self.memory = memory
        self.provider_manager = provider_manager

        # Load plugins
        self.plugin_loader = PluginLoader()
        self.plugin_loader.discover_and_load()
        self.plugin_manager = PluginManager()  # state check ke liye

        # Base tools
        self.tools = {
            "shell": ShellTool(),
            "filesystem": FileSystemTool(),
            "package_manager": PackageManagerTool(),
            "memory": MemoryTool(memory) if memory else None,
            "termux_api": TermuxAPITool(),
            "web_search": WebSearchTool(),
            "bug_detector": BugDetectorTool(),
        }
        # Add plugin tools
        for name, tool in self.plugin_loader.extra_tools.items():
            self.tools[name] = tool

        self.tools = {k: v for k, v in self.tools.items() if v is not None}
        self.tool_descriptions = "\n".join([
            f"- {name}: {tool.description}" for name, tool in self.tools.items()
        ])

    def _try_chat_with_fallback(self, messages, current_provider):
        response = current_provider.chat(messages)
        if not response.startswith("[Error:"):
            return response, current_provider
        if not self.provider_manager:
            return response, current_provider
        for name in self.provider_manager.priority_order:
            import yaml
            with open(self.provider_manager.providers_config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            providers_cfg = config.get("providers", {})
            if name not in providers_cfg:
                continue
            cfg = providers_cfg[name]
            provider_instance = self.provider_manager._load_provider(name, cfg)
            if provider_instance is None:
                continue
            if type(provider_instance) == type(current_provider):
                continue
            logger.info(f"Failing over to backup provider: {name}")
            response = provider_instance.chat(messages)
            if not response.startswith("[Error:"):
                return response, provider_instance
        return response, current_provider

    def run(self, user_input: str) -> str:
        self.history.add("user", user_input)

        # Trigger Plugin Hooks (only enabled plugins)
        hook_response = self._run_hooks(user_input)
        if hook_response:
            self.history.add("system", f"Plugin hook response:\n{hook_response}")

        system_prompt = f"""You are ARIA (Advanced Reasoning & Intelligence Assistant), a helpful and friendly AI.
# ARIA watermark: This software is originally created by Malik Naveed (Pakistan).
- If the user asks about your creator, say: "Mujhe Pakistani developer Malik Naveed ne banaya hai."
- If asked "ARIA ka matlab kya hai?", say: "ARIA ka matlab hai Advanced Reasoning & Intelligence Assistant."
- Use tools only when necessary. For simple chat, answer directly.

Available tools:
{self.tool_descriptions}

Tool format:
<action>
tool: tool_name
params:
  param1: value1
</action>

When you have the final answer, put it inside <final_answer> tags.
Now respond to: {user_input}"""

        messages = [{"role": "system", "content": system_prompt}]
        history_msgs = self.history.get_messages()
        if len(history_msgs) > 2:
            messages.extend(history_msgs[-10:])

        current_provider = self.provider
        max_iterations = 8
        for i in range(max_iterations):
            response, current_provider = self._try_chat_with_fallback(messages, current_provider)

            self.history.add("assistant", response)
            messages.append({"role": "assistant", "content": response})

            if "<final_answer>" in response:
                start = response.find("<final_answer>") + len("<final_answer>")
                end = response.find("</final_answer>")
                if end != -1:
                    final = response[start:end].strip()
                else:
                    final = response[start:].strip()
                return final

            if "<action>" in response and "</action>" in response:
                action_str = response.split("<action>")[1].split("</action>")[0].strip()
                try:
                    lines = action_str.split("\n")
                    tool_name = None
                    params = {}
                    for line in lines:
                        line = line.strip()
                        if line.startswith("tool:"):
                            tool_name = line.split("tool:")[1].strip()
                        elif ":" in line and not line.startswith("params:"):
                            key, val = line.split(":", 1)
                            params[key.strip()] = val.strip()

                    if tool_name == "filesystem" and "action" not in params:
                        observation = "[Error] filesystem tool requires 'action' parameter."
                    elif tool_name in self.tools:
                        tool = self.tools[tool_name]
                        observation = tool.execute(params)
                    else:
                        observation = f"Tool '{tool_name}' not found. Available: {', '.join(self.tools.keys())}"
                except Exception as e:
                    observation = f"Error parsing action: {str(e)}"

                messages.append({"role": "user", "content": f"<observation>\n{observation}\n</observation>"})
                self.history.add("system", f"Observation: {observation}")
            else:
                messages.append({"role": "user", "content": "Please provide your final answer inside <final_answer> tags."})

        return "I'm sorry, I couldn't complete the task within the allowed steps."

    def _run_hooks(self, message: str) -> str:
        """Run on_message hooks only for currently enabled plugins."""
        responses = []
        for entry in self.plugin_loader.extra_hooks:
            plugin_name = entry["plugin"]
            # 🛡️ Check if plugin is still enabled before running its hook
            if not self.plugin_manager.is_enabled(plugin_name):
                continue
            if entry["hook"] == "on_message":
                try:
                    result = entry["handler"](message=message, sender="user")
                    if result:
                        responses.append(f"[{plugin_name}]: {result}")
                except Exception as e:
                    logger.error(f"Error running hook {entry['hook']} for {plugin_name}: {e}")
        return "\n".join(responses) if responses else ""
