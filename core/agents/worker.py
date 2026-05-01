from tools.shell import ShellTool
from tools.filesystem import FileSystemTool
from tools.package_manager import PackageManagerTool
from tools.memory import MemoryTool
from tools.termux_api import TermuxAPITool
from tools.web_search import WebSearchTool
from tools.bug_detector import BugDetectorTool
from plugins.loader import PluginLoader
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter

logger = get_logger(__name__)

class Worker:
    def __init__(self, provider, memory=None):
        self.provider = provider
        self.tools = {
            "shell": ShellTool(),
            "filesystem": FileSystemTool(),
            "package_manager": PackageManagerTool(),
            "memory": MemoryTool(memory) if memory else None,
            "termux_api": TermuxAPITool(),
            "web_search": WebSearchTool(),
            "bug_detector": BugDetectorTool(),
        }
        # Load plugin tools
        loader = PluginLoader()
        loader.discover_and_load()
        for name, tool in loader.extra_tools.items():
            self.tools[name] = tool

        self.tools = {k: v for k, v in self.tools.items() if v is not None}
        self.tool_descriptions = "\n".join([
            f"- {name}: {tool.description}" for name, tool in self.tools.items()
        ])
        self.rate_limiter = RateLimiter(min_interval=0.7)

    def execute(self, subtask: str) -> str:
        # ... (existing worker code, unchanged)
        # To keep this short, we'll reuse the exact execute method from before
        # but we must ensure the Worker's execute uses self.tools correctly.
        # We'll inline the same logic but with preemptive search and retry.
        # For brevity, I'll write a clean version:
        info_keywords = ["weather", "mausam", "temperature", "news", "today", "current",
                         "latest", "aaj", "abhi", "haal", "khabar", "recipe", "tareeka"]
        preemptive_result = None
        if any(kw in subtask.lower() for kw in info_keywords):
            logger.info("Worker: Subtask requires real-time info — running preemptive web_search.")
            search_tool = self.tools.get("web_search")
            if search_tool:
                self.rate_limiter.wait_sync()
                preemptive_result = search_tool.execute({"query": subtask})

        result = self._attempt(subtask, None, preemptive_result)
        if self._is_missing_info(result):
            logger.info("Worker detected missing info — retrying with mandatory web_search.")
            feedback = "Your previous answer lacked the requested information. You MUST use the web_search tool now. Provide the final answer inside <final_answer> tags."
            result = self._attempt(subtask, feedback, preemptive_result)
        return result

    def _attempt(self, subtask: str, feedback: str = None, preemptive_result: str = None) -> str:
        system_prompt = f"""You are a helpful AI worker agent. Solve the given subtask.
- For any real-time information, you MUST use the web_search tool first.
- Provide the final answer inside <final_answer> tags.
- Do NOT say "I don't have" or "not available" — use web_search instead.

Available tools:
{self.tool_descriptions}

Tool format:
<action>
tool: tool_name
params:
  param1: value1
</action>

Subtask: {subtask}"""

        messages = [{"role": "system", "content": system_prompt}]
        if preemptive_result and not preemptive_result.startswith("[Error"):
            messages.append({"role": "user", "content": f"<observation>\nPre-fetched web search result:\n{preemptive_result[:800]}\n</observation>"})
        user_msg = feedback if feedback else "Please solve the subtask."
        messages.append({"role": "user", "content": user_msg})

        for i in range(4):
            self.rate_limiter.wait_sync()
            response = self.provider.chat(messages)
            messages.append({"role": "assistant", "content": response})

            if "<final_answer>" in response:
                start = response.find("<final_answer>") + len("<final_answer>")
                end = response.find("</final_answer>")
                if end != -1:
                    return response[start:end].strip()
                else:
                    return response[start:].strip()

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
                    if tool_name in self.tools:
                        observation = self.tools[tool_name].execute(params)
                    else:
                        observation = f"Tool '{tool_name}' not found. Available: {', '.join(self.tools.keys())}"
                except Exception as e:
                    observation = f"Error parsing action: {str(e)}"
                messages.append({"role": "user", "content": f"<observation>\n{observation}\n</observation>"})
            else:
                messages.append({"role": "user", "content": "Please provide your final answer inside <final_answer> tags."})

        last_response = messages[-1]["content"] if messages else ""
        if "<final_answer>" in last_response:
            start = last_response.find("<final_answer>") + len("<final_answer>")
            end = last_response.find("</final_answer>")
            return last_response[start:end].strip() if end != -1 else last_response[start:].strip()
        return f"[Worker did not complete subtask: {subtask}]"

    def _is_missing_info(self, text: str) -> bool:
        missing_phrases = [
            "i don't have", "not available", "unable to", "no information",
            "no current", "could not find", "no weather", "not completed",
            "did not complete", "was not completed", "wasn't provided"
        ]
        lower_text = text.lower()
        return any(phrase in lower_text for phrase in missing_phrases)
