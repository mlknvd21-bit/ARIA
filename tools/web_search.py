import re
import json
import subprocess
from tools.base import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the internet for real-time information including weather, news, facts. Uses wttr.in for weather, Wikipedia for facts, and DuckDuckGo as fallback."
        )

    def execute(self, params: dict) -> str:
        query = params.get("query", "").strip()
        if not query:
            return "[Error] No search query provided."

        lower_query = query.lower()

        # 1. For weather queries, ALWAYS use wttr.in first (very reliable)
        if any(word in lower_query for word in ["weather", "mausam", "temperature", "barish", "dhoop", "mausam"]):
            weather_result = self._get_weather(query)
            if weather_result and not weather_result.startswith("[Error"):
                return weather_result

        # 2. For general knowledge, try Wikipedia
        wiki_result = self._search_wikipedia(query)
        if wiki_result and not wiki_result.startswith("[Error") and wiki_result is not None:
            return wiki_result

        # 3. Fallback to DuckDuckGo
        return self._search_duckduckgo(query)

    def _get_weather(self, query: str) -> str:
        """Fetch weather using wttr.in — returns plain text, no API key needed."""
        try:
            # Extract city name (simple approach: take the query as is, wttr.in handles it)
            city = query.replace("weather", "").replace("mausam", "").replace("temperature", "").strip()
            if not city:
                city = query.strip()
            # Clean city name for URL
            city_encoded = city.replace(" ", "+")
            cmd = [
                "curl", "-s", "-L",
                "--max-time", "8",
                f"https://wttr.in/{city_encoded}?format=3"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if result.returncode == 0 and result.stdout.strip():
                weather_text = result.stdout.strip()
                # If wttr.in returns a message about unknown location, return None
                if "Unknown location" not in weather_text and len(weather_text) > 5:
                    return f"Weather for {city}:\n{weather_text}"
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _search_wikipedia(self, query: str) -> str:
        """Search Wikipedia using the REST API."""
        try:
            import urllib.parse
            encoded = urllib.parse.quote(query)
            cmd = [
                "curl", "-s", "-L",
                "--max-time", "10",
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout)
            if "extract" in data:
                extract = data["extract"][:500]
                title = data.get("title", query)
                return f"Wikipedia ({title}):\n{extract}"
            elif "detail" in data:
                return None
            return None
        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    def _search_duckduckgo(self, query: str) -> str:
        """Fallback: DuckDuckGo lite search."""
        try:
            cmd = [
                "curl", "-s", "-L",
                "--max-time", "10",
                f"https://lite.duckduckgo.com/lite/?q={query.replace(' ', '+')}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                return f"[Error] curl failed: {result.stderr}"
            html = result.stdout.strip()
            if not html:
                return "[No results found.]"
            snippets = re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL)
            clean = []
            for s in snippets:
                txt = re.sub(r'<[^>]+>', '', s).strip()
                if txt and len(txt) > 10:
                    clean.append(txt)
            if not clean:
                visible = re.sub(r'<[^>]+>', ' ', html)
                visible = re.sub(r'\s+', ' ', visible).strip()
                if len(visible) > 10:
                    clean = [visible[:500]]
            top = clean[:3]
            return "\n---\n".join(top) if top else "[No meaningful results extracted.]"
        except subprocess.TimeoutExpired:
            return "[Error] Search timed out."
        except Exception as e:
            return f"[Error] {str(e)}"
