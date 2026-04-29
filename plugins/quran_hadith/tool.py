import json, os, re, httpx
from tools.base import BaseTool

class QuranHadithTool(BaseTool):
    def __init__(self):
        super().__init__(name="quran_hadith_tool", description="Quran & Hadith via live APIs.")
        self.quran_cache = {}
        self.juz_cache = []

    def execute(self, params: dict) -> str:
        action = params.get("action", "").strip().lower()
        if action == "quran_list_surahs":
            return self._list_surahs()
        elif action == "quran_list_juzs":
            return self._list_juzs()
        elif action == "quran_get_ayahs":
            surah = params.get("surah", "1").strip()
            return self._get_surah_ayahs(surah)
        elif action == "quran_get_juz":
            juz = params.get("juz", "1").strip()
            return self._get_juz_ayahs(juz)
        elif action == "quran_tafsir":
            surah = params.get("surah", "1").strip()
            ayah = params.get("ayah", "1").strip()
            return self._get_tafsir(surah, ayah)
        elif action == "hadith":
            return "[Hadith module coming tomorrow]"
        return "[Error] Unknown action."

    def _call_api(self, url):
        try:
            resp = httpx.get(url, timeout=10)
            return resp.json()
        except:
            return {}

    def _list_surahs(self):
        if "surahs" not in self.quran_cache:
            data = self._call_api("https://api.alquran.cloud/v1/surah")
            self.quran_cache["surahs"] = data.get("data", [])
        surahs = self.quran_cache["surahs"]
        return json.dumps([{"number": s["number"], "name_ar": s["name"], "name_en": s["englishName"], "ayahs": s["numberOfAyahs"]} for s in surahs], ensure_ascii=False)

    def _list_juzs(self):
        if not self.juz_cache:
            data = self._call_api("https://api.alquran.cloud/v1/juz")
            self.juz_cache = [{"number": j["number"], "start": f"{j['start']['surah']}:{j['start']['ayah']}", "end": f"{j['end']['surah']}:{j['end']['ayah']}"} for j in data.get("data", [])]
        return json.dumps(self.juz_cache, ensure_ascii=False)

    def _get_surah_ayahs(self, surah):
        data = self._call_api(f"https://api.alquran.cloud/v1/surah/{surah}/editions/ar.asad,ur.jalandhri,en.sahih")
        editions = data.get("data", [])
        arabic = next((e for e in editions if "ar" in e["edition"]["identifier"]), None)
        urdu = next((e for e in editions if "ur" in e["edition"]["identifier"]), None)
        english = next((e for e in editions if "en" in e["edition"]["identifier"]), None)
        result = []
        if arabic:
            for a in arabic.get("ayahs", []):
                num = a["numberInSurah"]
                urdu_text = next((u["text"] for u in urdu["ayahs"] if u["numberInSurah"]==num), "") if urdu else ""
                en_text = next((e["text"] for e in english["ayahs"] if e["numberInSurah"]==num), "") if english else ""
                result.append({"number": num, "arabic": a["text"], "urdu": urdu_text, "en": en_text})
        return json.dumps(result, ensure_ascii=False)

    def _get_juz_ayahs(self, juz):
        data = self._call_api(f"https://api.alquran.cloud/v1/juz/{juz}/editions/ar.asad,ur.jalandhri,en.sahih")
        editions = data.get("data", [])
        arabic = next((e for e in editions if "ar" in e["edition"]["identifier"]), None)
        urdu = next((e for e in editions if "ur" in e["edition"]["identifier"]), None)
        english = next((e for e in editions if "en" in e["edition"]["identifier"]), None)
        result = []
        if arabic:
            for a in arabic.get("ayahs", []):
                num = a["numberInSurah"]
                surah_num = a.get("surah", {}).get("number", "")
                urdu_text = next((u["text"] for u in urdu["ayahs"] if u["numberInSurah"]==num and u.get("surah",{}).get("number")==surah_num), "") if urdu else ""
                en_text = next((e["text"] for e in english["ayahs"] if e["numberInSurah"]==num and e.get("surah",{}).get("number")==surah_num), "") if english else ""
                result.append({"number": f"{surah_num}:{num}", "arabic": a["text"], "urdu": urdu_text, "en": en_text})
        return json.dumps(result, ensure_ascii=False)

    def _get_tafsir(self, surah, ayah):
        data = self._call_api(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/editions/ur.jalandhri,en.sahih,ar.tafsir_jalalayn")
        editions = data.get("data", [])
        tafsir = next((e for e in editions if "tafsir" in e["edition"]["identifier"]), None)
        if tafsir:
            return json.dumps({"tafsir": tafsir["text"]}, ensure_ascii=False)
        return json.dumps({"tafsir": "Tafsir not available."})

    def handle_command(self, command, args):
        return "Use Web GUI for full features."

    def get_widget_html(self, widget_name):
        if widget_name == "quran_hadith_widget":
            return """
<div style="display:flex; gap:20px; flex-wrap:wrap;">
    <div class="card" style="flex:1; min-width:300px;">
        <h4>📖 Quran</h4>
        <select id="quran-type" onchange="toggleQuranType()" style="width:100%; padding:8px; margin-bottom:5px;">
            <option value="surah">By Surah</option>
            <option value="juz">By Juz (Para)</option>
        </select>
        <select id="quran-list" style="width:100%; padding:8px; margin-bottom:5px;"></select>
        <button onclick="loadQuranAyahs()" style="background:#4CAF50; color:white; padding:10px; border:none; width:100%;">Load Ayahs</button>
        <div id="quran-ayahs" style="margin-top:10px; max-height:400px; overflow-y:auto; white-space:pre-wrap; background:white; padding:8px; border:1px solid #eee;"></div>
        <div id="quran-tafsir" style="margin-top:5px; padding:8px; background:#f9f9f9; border:1px solid #ddd; display:none;"></div>
    </div>
    <div class="card" style="flex:1; min-width:300px;">
        <h4>📜 Hadith (Coming Tomorrow)</h4>
    </div>
</div>
"""
        return ""
