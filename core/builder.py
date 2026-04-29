import re
import os
import time
from utils.logger import get_logger
from core.history import ConversationHistory
from providers.manager import ProviderManager

logger = get_logger(__name__)

class Builder:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
        self.base_path = os.path.join(os.path.expanduser("~"), "aria_projects")
        os.makedirs(self.base_path, exist_ok=True)

    def build(self, description: str) -> str:
        """Create a web app from a user description. Returns a success/error message."""
        # Generate a project name from description (slug)
        project_name = self._generate_project_name(description)
        project_path = os.path.join(self.base_path, project_name)

        # Build the LLM prompt
        system_prompt = """You are an expert web developer. Create a complete, single-page web application based on the user's request.
The app MUST be fully functional and tested. All buttons, inputs, and interactions MUST work. Use clean, semantic HTML, modern CSS, and vanilla JavaScript. No placeholders, no incomplete code. Ensure every click handler is implemented and every function is defined.
Provide the full code for each file, enclosed in the following format:

---FILE: filename.ext---
file content here
---FILE: anotherfile.ext---
content here

Allowed extensions: .html, .css, .js, .py, .txt, .md.
Only these files will be saved; any other output will be ignored.
If you need to create a Python script, make it small and self-contained.
The first file should be index.html.
Ensure the code is complete, functional, and well-commented.
Do not include any extra text outside the file delimiters."""
        user_prompt = f"Create a web app that does: {description}"

        # Try to get response via failover
        response = self._call_llm_with_fallback(system_prompt, user_prompt)
        if response.startswith("[Error:"):
            return f"Build failed: {response}"

        # Parse the response for files
        files = self._parse_files(response)
        if not files:
            return "Build failed: No valid files found in the LLM response. Make sure the description is clear and try again."

        # Validate file names
        for filename in list(files.keys()):
            if not self._is_safe_filename(filename):
                return f"Build failed: Unsafe or unsupported filename '{filename}'."

        # Create project directory (avoid overwriting)
        if os.path.exists(project_path):
            # Append timestamp to name
            project_name = f"{project_name}_{int(time.time())}"
            project_path = os.path.join(self.base_path, project_name)

        try:
            os.makedirs(project_path, exist_ok=False)
        except OSError as e:
            return f"Build failed: Unable to create project directory. {e}"

        # Write files
        for filename, content in files.items():
            filepath = os.path.join(project_path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        # Generate a simple README.md
        readme_path = os.path.join(project_path, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {project_name}\n\n{description}\n\nBuilt by ARIA.\n")

        return f"Project '{project_name}' created successfully. View it in the Projects tab or run directly."

    def _generate_project_name(self, description: str) -> str:
        """Create a safe directory name from the description."""
        # Remove non-alphanumeric, replace spaces with underscores, lowercase
        name = re.sub(r'[^a-zA-Z0-9_ ]', '', description)
        name = name.strip().lower().replace(' ', '_')
        # Limit length
        if len(name) > 40:
            name = name[:40]
        # If empty or only underscores, use 'new_project'
        name = name.strip('_')
        if not name:
            name = "new_project"
        return f"app_{name}"

    def _is_safe_filename(self, filename: str) -> bool:
        """Check that filename has no path separators and uses allowed extensions."""
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        allowed_exts = ['.html', '.css', '.js', '.py', '.txt', '.md']
        return any(filename.lower().endswith(ext) for ext in allowed_exts)

    def _parse_files(self, text: str) -> dict:
        """Extract filename and content from delimited text."""
        pattern = r'---FILE:\s*(.+?)\s*---\s*?(.*?)(?=---FILE:|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        files = {}
        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()
            if filename:
                files[filename] = content
        return files

    def _call_llm_with_fallback(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM using the provider manager with failover."""
        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        # Try all enabled providers in priority order
        for name in self.provider_manager.priority_order:
            # Load provider
            import yaml
            with open(self.provider_manager.providers_config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            providers_cfg = config.get("providers", {})
            if name not in providers_cfg:
                continue
            cfg = providers_cfg[name]
            provider = self.provider_manager._load_provider(name, cfg)
            if provider is None:
                continue
            logger.info(f"Builder using provider: {name}")
            try:
                response = provider.chat(msgs)
                if not response.startswith("[Error:"):
                    return response
                # else error, try next
                logger.warning(f"Provider {name} failed: {response}")
            except Exception as e:
                logger.error(f"Provider {name} exception: {e}")
        return "[Error: All providers failed to respond.]"
