import os
import re
import ast
import json
import yaml
import py_compile
from tools.base import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

class BugDetectorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="bug_detector",
            description="Smart multi‑format scanner with context‑aware rules."
        )

    def execute(self, params: dict) -> str:
        action = params.get("action", "").strip().lower()
        if action == "scan":
            target = params.get("path", os.path.expanduser("~/aria"))
            if not os.path.isdir(target):
                return "[Error] Target directory not found."
            issues = self.scan(target)
            if not issues:
                return "✅ No issues found! Your project looks clean."
            return self._format_report(issues)
        return "[Error] Unknown action. Use 'scan'."

    def scan(self, base_dir):
        issues = []
        exclude = {'__pycache__','.git','backups','data','quran_data','venv','env','node_modules'}
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude]
            for f in files:
                fp = os.path.join(root, f)
                if f.endswith('.py'):
                    self._check_python(fp, issues)
                elif f.endswith('.html') or f.endswith('.htm'):
                    self._check_html(fp, issues)
                elif f.endswith('.js'):
                    self._check_javascript(fp, issues)
                elif f.endswith('.css'):
                    self._check_css(fp, issues)
                elif f.endswith('.json'):
                    self._check_json(fp, issues)
                elif f.endswith('.yaml') or f.endswith('.yml'):
                    self._check_yaml(fp, issues)
                elif f.endswith('.md'):
                    self._check_markdown(fp, issues)
        return issues

    # -----------------------------------------------------------------
    # Python
    # -----------------------------------------------------------------
    def _check_python(self, filepath, issues):
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            issues.append({"file": filepath, "line": self._extract_line(e),
                "issue": "Syntax Error", "severity": "Critical", "suggestion": str(e)})
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except Exception as e:
            issues.append({"file": filepath, "line": 0, "issue": "AST Error",
                "severity": "Warning", "suggestion": str(e)})
            return

        class PyVisitor(ast.NodeVisitor):
            def visit_ExceptHandler(self, node):
                if node.type is None:
                    issues.append({"file": filepath, "line": node.lineno,
                        "issue": "Bare except", "severity": "Warning",
                        "suggestion": "Use 'except Exception:' instead of bare 'except:'."})
                self.generic_visit(node)
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in ('eval','exec'):
                    issues.append({"file": filepath, "line": node.lineno,
                        "issue": f"Use of {node.func.id}()", "severity": "High",
                        "suggestion": "Avoid eval/exec for security."})
                self.generic_visit(node)
        PyVisitor().visit(tree)

    # -----------------------------------------------------------------
    # HTML (improved – self‑closing tags ignored)
    # -----------------------------------------------------------------
    def _check_html(self, filepath, issues):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            void_tags = {'area','base','br','col','embed','hr','img','input',
                         'link','meta','param','source','track','wbr'}
            all_tags = re.findall(r'<(/?)(\w+)[^>]*>', content)
            stack = []
            for slash, tag_name in all_tags:
                tag_name = tag_name.lower()
                if tag_name in void_tags:
                    continue
                if slash == '':
                    stack.append(tag_name)
                else:
                    if stack and stack[-1] == tag_name:
                        stack.pop()
            if stack:
                issues.append({"file": filepath, "line": 1,
                    "issue": "Potentially unclosed HTML tags", "severity": "Warning",
                    "suggestion": f"Unclosed tags: {', '.join(stack)}"})
            imgs = re.findall(r'<img[^>]+>', content)
            for img in imgs:
                if 'alt=' not in img:
                    issues.append({"file": filepath, "line": 1,
                        "issue": "Image without alt attribute", "severity": "Info",
                        "suggestion": "Add alt text for accessibility."})
                    break
        except Exception:
            pass

    # -----------------------------------------------------------------
    # JavaScript (smarter – only report alert/console.log outside functions)
    # -----------------------------------------------------------------
    def _check_javascript(self, filepath, issues):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            inside_function = False
            for idx, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('function ') or 'function(' in stripped:
                    inside_function = True
                if inside_function and stripped.startswith('}'):
                    inside_function = False
                if not inside_function and (re.search(r'\balert\b', stripped) or re.search(r'\bconsole\.log\b', stripped)):
                    issues.append({"file": filepath, "line": idx,
                        "issue": "Debug statement outside function", "severity": "Info",
                        "suggestion": "Remove or disable console.log/alert for production."})
                    break
        except Exception:
            pass

    # -----------------------------------------------------------------
    # CSS
    # -----------------------------------------------------------------
    def _check_css(self, filepath, issues):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            empty = re.findall(r'([^{]+)\{\s*\}', content)
            if empty:
                issues.append({"file": filepath, "line": 1,
                    "issue": f"{len(empty)} empty CSS ruleset(s)", "severity": "Info",
                    "suggestion": "Remove empty rulesets to keep CSS clean."})
        except Exception:
            pass

    # -----------------------------------------------------------------
    # JSON
    # -----------------------------------------------------------------
    def _check_json(self, filepath, issues):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append({"file": filepath, "line": e.lineno,
                "issue": "Invalid JSON", "severity": "Critical",
                "suggestion": str(e)})
        except Exception:
            pass

    # -----------------------------------------------------------------
    # YAML
    # -----------------------------------------------------------------
    def _check_yaml(self, filepath, issues):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            issues.append({"file": filepath, "line": 1,
                "issue": "Invalid YAML", "severity": "Critical",
                "suggestion": str(e)})
        except Exception:
            pass

    # -----------------------------------------------------------------
    # Markdown (smarter – GitHub‑valid relative links are fine)
    # -----------------------------------------------------------------
    def _check_markdown(self, filepath, issues):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            broken = []
            for text, url in links:
                # Skip absolute URLs, anchors, and GitHub‑valid relative links
                if url.startswith('http') or url.startswith('#'):
                    continue
                if url.startswith('/'):
                    continue
                # Allow common GitHub files that exist in the repo root
                common_files = {'LICENSE', 'COMING_SOON.md', 'SECURITY.md', 'README.md'}
                if url in common_files:
                    continue
                # Check if the file actually exists relative to the repo root
                abs_url = os.path.join(os.path.dirname(filepath), url)
                if os.path.exists(abs_url) or os.path.exists(os.path.join(os.path.expanduser('~/aria'), url)):
                    continue
                broken.append(f"{text} -> {url}")
            if broken:
                issues.append({"file": filepath, "line": 1,
                    "issue": f"{len(broken)} potentially broken link(s)", "severity": "Warning",
                    "suggestion": ". ".join(broken[:3])})
        except Exception:
            pass

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------
    def _extract_line(self, error):
        m = re.search(r'line (\d+)', str(error))
        return int(m.group(1)) if m else 0

    def _format_report(self, issues):
        if not issues:
            return "✅ No issues found! Your project looks clean."
        lines = [f"🔍 Found {len(issues)} issue(s):\n"]
        for i, iss in enumerate(issues, 1):
            short = iss['file'].replace(os.path.expanduser('~/aria/'), '')
            lines.append(f"--- Bug {i} ---")
            lines.append(f"File: {short}")
            lines.append(f"Line: {iss['line']}")
            lines.append(f"Issue: {iss['issue']} | Severity: {iss['severity']}")
            lines.append(f"Suggestion: {iss['suggestion']}\n")
        return "\n".join(lines)
