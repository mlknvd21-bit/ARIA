import json
import os
import re
from tools.base import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "electronics_parts.json")

class ElectronicsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="electronics_parts",
            description="Search electronics components database."
        )
        self.database = self._load_database()

    def _load_database(self):
        try:
            with open(DATABASE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def execute(self, params: dict) -> str:
        part = params.get("part", "").strip().lower()
        if not part:
            return "[Error] Please specify a part number."
        return self._lookup(part)

    def _lookup(self, part: str) -> str:
        if part in self.database:
            return self._format_part(part, self.database[part])
        suggestions = [k for k in self.database if part in k]
        if suggestions:
            return f"No exact match for '{part}'. Did you mean: {', '.join(suggestions)}?"
        return f"Part '{part}' not found in database."

    def _format_part(self, part: str, data: dict) -> str:
        lines = [f"📦 {part.upper()} ({data.get('type', 'Unknown')})"]
        for key, val in data.items():
            if key == "alternatives":
                lines.append(f"   🔄 Alternatives: {', '.join(val)}")
            elif key == "uses":
                lines.append(f"   ⚙️ Uses: {val}")
            elif key == "type":
                continue
            else:
                lines.append(f"   📋 {key}: {val}")
        return "\n".join(lines)

    def get_widget_html(self, widget_name: str) -> str:
        if widget_name == "electronics_search":
            return """
            <div style="padding:10px;">
                <h4>🔍 Search Electronics Parts</h4>
                <input type="text" id="electronics-widget-input" placeholder="Enter part number (e.g., 2N2222, LM358)" style="width:80%; padding:8px;">
                <button onclick="searchElectronicsWidget()" style="padding:8px 16px; background:#4CAF50; color:white; border:none; cursor:pointer;">Search</button>
                <div id="electronics-widget-result" style="margin-top:10px; padding:8px; border:1px solid #ccc; min-height:50px; white-space:pre-wrap;"></div>
            </div>
            """
        return ""

    def on_message(self, message: str, sender: str = "user"):
        part_pattern = re.compile(
            r'\b(?:2N\d{2,5}|BC\d{2,5}|IRF\d{2,5}|LM\d{2,5}|NE\d{2,5}|'
            r'1N\d{2,5}|TL\d{2,5}|MC\d{2,5}|UA\d{2,5}|'
            r'arduino_\w+|esp32|raspberry\s?pi\s?\w*)\b',
            re.IGNORECASE
        )
        matches = part_pattern.findall(message)
        if not matches:
            return None
        responses = []
        for match in matches[:2]:
            part_lower = match.lower()
            if part_lower in self.database:
                responses.append(self._format_part(part_lower, self.database[part_lower]))
            else:
                suggestions = [k for k in self.database if part_lower in k]
                if suggestions:
                    responses.append(f"ℹ️ '{match}' not found. Did you mean: {', '.join(suggestions)}?")
        return "\n\n".join(responses) if responses else None
