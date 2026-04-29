import subprocess
import json
import os
import re
from tools.base import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

class TermuxAPITool(BaseTool):
    def __init__(self):
        super().__init__(
            name="termux_api",
            description="Access Android device features via Termux:API. Actions: battery, location, sms_send, notify, camera, microphone, wifi_scan, wifi_connection, media, sms_inbox, alarm, schedule_notify, speech_to_text (lang='en' or 'ur'), text_to_speech (text, lang='en' or 'ur')."
        )

    def execute(self, params: dict) -> str:
        action = params.get("action", "").strip().lower()
        if not action:
            return "[Error] No action specified."

        try:
            # ----- Battery -----
            if action == "battery":
                return self._run_json("termux-battery-status")

            # ----- Location -----
            elif action == "location":
                data = self._run_json("termux-location", timeout=15)
                if data:
                    return f"Lat: {data.get('latitude')}, Lon: {data.get('longitude')}, Alt: {data.get('altitude', 'N/A')}m, Speed: {data.get('speed', 'N/A')}m/s"
                return "[Error] Could not get location."

            # ----- SMS Send -----
            elif action == "sms_send":
                number = params.get("number", "")
                text = params.get("text", "")
                if not number or not text:
                    return "[Error] SMS requires 'number' and 'text'."
                cmd = ["termux-sms-send", "-n", number, text]
                _, err = self._run_cmd(cmd)
                return "SMS sent." if not err else f"[Error] {err}"

            # ----- Notification -----
            elif action == "notify":
                title = params.get("title", "ARIA")
                body = params.get("body", "")
                if not body:
                    return "[Error] Notification requires 'body'."
                cmd = ["termux-notification", "-t", title, "-c", body]
                _, err = self._run_cmd(cmd)
                return "Notification sent." if not err else f"[Error] {err}"

            # ----- Camera -----
            elif action == "camera":
                save_dir = os.path.expanduser("~/storage/pictures")
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, "aria_photo.jpg")
                cmd = ["termux-camera-photo", save_path]
                _, err = self._run_cmd(cmd, timeout=15)
                if err:
                    return f"[Error] {err}"
                self._run_cmd(["termux-media-scan", save_path], timeout=10)
                return f"Photo saved to {save_path}"

            # ----- Microphone -----
            elif action == "microphone":
                save_dir = os.path.expanduser("~/storage/music")
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, "aria_record.mp3")
                limit = params.get("limit", "5")
                cmd = ["termux-microphone-record", "-f", save_path, "-l", limit]
                _, err = self._run_cmd(cmd, timeout=int(limit)+2)
                return f"Recording saved to {save_path}" if not err else f"[Error] {err}"

            # ----- WiFi Scan -----
            elif action == "wifi_scan":
                data = self._run_json("termux-wifi-scaninfo", timeout=10)
                if data and isinstance(data, list):
                    lines = [f"{net.get('ssid', '?')} (strength: {net.get('strength', '?')}dBm)" for net in data[:5]]
                    return "\n".join(lines) if lines else "[No WiFi networks found.]"
                return "[Error] Could not scan WiFi."

            # ----- WiFi Connection -----
            elif action == "wifi_connection":
                data = self._run_json("termux-wifi-connectioninfo", timeout=8)
                if data:
                    ssid = data.get("ssid", "N/A")
                    bssid = data.get("bssid", "N/A")
                    ip = data.get("ip", "N/A")
                    speed = data.get("link_speed", "N/A")
                    return f"SSID: {ssid}, BSSID: {bssid}, IP: {ip}, Speed: {speed}Mbps"
                return "[Error] Could not get WiFi connection info."

            # ----- Media -----
            elif action == "media":
                subcmd = params.get("command", "").strip().lower()
                valid = ["play","pause","stop","next","prev","info"]
                if subcmd not in valid:
                    return f"[Error] Media command must be one of {', '.join(valid)}"
                out, err = self._run_cmd(["termux-media-player", subcmd], timeout=8)
                if subcmd == "info" and out:
                    return out.strip()
                return f"Media {subcmd} successful." if not err else f"[Error] {err}"

            # ----- SMS Inbox -----
            elif action == "sms_inbox":
                data = self._run_json("termux-sms-list", timeout=10)
                if data and isinstance(data, list):
                    msgs = [f"{m.get('number','?')} ({m.get('date','?')}): {m.get('body','?')}" for m in data[:5]]
                    return "\n".join(msgs) if msgs else "[Inbox empty]"
                return "[Error] Could not read SMS inbox."

            # ----- Alarm -----
            elif action == "alarm":
                time_ms = params.get("time_ms", "")
                title = params.get("title", "ARIA Alarm")
                if not time_ms:
                    return "[Error] Alarm requires 'time_ms'."
                cmd = ["termux-alarm", "-t", time_ms, "-n", title]
                _, err = self._run_cmd(cmd, timeout=10)
                return f"Alarm set for {time_ms}." if not err else f"[Error] {err}"

            # ----- Schedule Notify -----
            elif action == "schedule_notify":
                time_str = params.get("time", "")
                message = params.get("message", "")
                if not time_str or not message:
                    return "[Error] schedule_notify requires 'time' (HH:MM) and 'message'."
                if not re.match(r"^\d{1,2}:\d{2}$", time_str):
                    return "[Error] Time format must be HH:MM (24-hour)."
                full_cmd = f'echo termux-notification -c "{message}" | at {time_str}'
                _, err = self._run_cmd(full_cmd, shell=True, timeout=10)
                return f"Notification scheduled for {time_str}." if not err else f"[Error] Scheduling failed: {err}"

            # ----- NEW: Speech to Text -----
            elif action == "speech_to_text":
                lang = params.get("lang", "en").strip()
                # Urdu uses 'ur' code; Termux-speech-to-text may not support 'ur', but we can try
                cmd = ["termux-speech-to-text"]
                if lang:
                    cmd.extend(["-l", lang])
                out, err = self._run_cmd(cmd, timeout=20)
                if out:
                    return out.strip()
                elif err:
                    return f"[Error] {err}"
                else:
                    return "[No speech recognized]"

            # ----- NEW: Text to Speech -----
            elif action == "text_to_speech":
                text = params.get("text", "")
                lang = params.get("lang", "en").strip()
                if not text:
                    return "[Error] 'text' required."
                cmd = ["termux-tts-speak"]
                if lang:
                    cmd.extend(["-l", lang])
                cmd.append(text)
                _, err = self._run_cmd(cmd, timeout=15)
                return "Spoken." if not err else f"[Error] {err}"

            else:
                return f"[Error] Unknown action: {action}"

        except Exception as e:
            return f"[Error] {str(e)}"

    def _run_json(self, command, timeout=10):
        try:
            result = subprocess.run([command], capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
            return None
        except Exception:
            return None

    def _run_cmd(self, cmd, timeout=10, shell=False):
        try:
            if shell:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout, result.stderr
        except Exception as e:
            return "", str(e)
