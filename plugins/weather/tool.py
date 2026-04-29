import subprocess
from tools.base import BaseTool

class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="weather_tool",
            description="Get current weather for any city using wttr.in."
        )

    def execute(self, params: dict) -> str:
        city = params.get("city", "").strip()
        if not city:
            return "[Error] Please provide a city name."
        return self._get_weather(city)

    def _get_weather(self, city: str) -> str:
        try:
            result = subprocess.run(
                ["curl", "-s", f"https://wttr.in/{city}?format=3"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return f"🌤️ Weather for {city}:\n{result.stdout.strip()}"
            return f"[Error] Could not fetch weather for '{city}'."
        except Exception as e:
            return f"[Error] {str(e)}"

    # ----- CLI handle_command -----
    def handle_command(self, command: str, args: str) -> str:
        """Handle direct CLI command /weather <city>."""
        if command == "/weather":
            city = args.strip()
            if not city:
                return "Usage: /weather <city>"
            return self._get_weather(city)
        return None  # unknown command

    # ----- ویب ویجیٹ -----
    def get_widget_html(self, widget_name: str) -> str:
        if widget_name == "weather_card":
            return """
            <div style="padding:10px;">
                <h4>🌤️ Weather</h4>
                <input type="text" id="weather-city-input" placeholder="Enter city name" style="width:80%; padding:8px;">
                <button onclick="searchWeatherWidget()" style="padding:8px 16px; background:#4CAF50; color:white; border:none; cursor:pointer;">Get Weather</button>
                <div id="weather-widget-result" style="margin-top:10px; padding:8px; border:1px solid #ccc; min-height:50px; white-space:pre-wrap;"></div>
            </div>
            """
        return ""
