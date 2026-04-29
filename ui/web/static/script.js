function openTab(evt, tabName) {
    var i, tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }
    var tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
    if (tabName === 'settings') { loadProviders(); loadModels(); loadMemory(); loadBackups(); }
    else if (tabName === 'projects') { loadProjects(); }
    else if (tabName === 'android') { loadBattery(); }
    else if (tabName === 'plugins') { loadPlugins(); }
}
document.getElementById("defaultOpen").click();
function toggleCollapse(id) { var c=document.getElementById(id); c.style.maxHeight=c.style.maxHeight&&c.style.maxHeight!=="0px"?"0px":c.scrollHeight+"px"; }

// ===================== CHAT =====================
function sendMessage() {
    var input = document.getElementById("chat-input"), msg = input.value.trim();
    if (!msg) return;
    var box = document.getElementById("chat-box");
    box.innerHTML += "<p><b>You:</b> " + msg + "</p>"; input.value = "";
    fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: msg }) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.response) box.innerHTML += "<p><b>ARIA:</b> " + d.response + "</p>";
        else box.innerHTML += "<p><b>Error:</b> " + (d.error || "") + "</p>";
        box.scrollTop = box.scrollHeight;
    })
    .catch(function(e) { box.innerHTML += "<p><b>Network error</b>"; });
}
document.getElementById("chat-input").addEventListener("keypress", function(e) { if (e.key === "Enter") sendMessage(); });

// ===================== SWARM =====================
function runSwarm() {
    var task = document.getElementById("swarm-input").value.trim();
    if (!task) { alert("Enter a task"); return; }
    var res = document.getElementById("swarm-result");
    res.textContent = "Running Swarm...";
    fetch("/api/swarm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task: task }) })
    .then(function(r) { return r.json(); })
    .then(function(d) { res.textContent = d.result || d.error || "No response"; });
}

// ===================== PROJECTS =====================
function loadProjects() {
    fetch("/api/projects").then(function(r) { return r.json(); }).then(function(data) {
        var html = "";
        if (Array.isArray(data) && data.length) {
            data.forEach(function(p) {
                html += '<div class="card"><b>' + p.name + '</b> (web: ' + (p.has_web ? "Yes" : "No") + ')';
                if (p.running) html += ' 🔵 Running on port ' + p.port + ' <button onclick="stopProject(\'' + p.name + '\')">Stop</button>';
                html += '<br><button onclick="runProject(\'' + p.name + '\')">Run</button> ';
                html += '<button onclick="toggleFiles(\'' + p.name + '\')">Files</button>';
                html += '<div id="files-' + p.name + '" style="display:none; margin-top:5px;"></div></div>';
            });
        } else html = "<p>No projects yet.</p>";
        document.getElementById("projects-list").innerHTML = html;
    });
}
function runProject(name) { fetch("/api/projects/" + name + "/run", { method: "POST" }).then(function(r) { return r.json(); }).then(function(d) { if (d.url) window.open(d.url, "_blank"); else alert("Error"); }); }
function stopProject(name) { fetch("/api/projects/" + name + "/stop", { method: "POST" }).then(function(r) { return r.json(); }).then(function() { loadProjects(); }); }
function toggleFiles(name) {
    var div = document.getElementById("files-" + name);
    if (div.style.display === "none" || div.style.display === "") {
        fetch("/api/projects/" + name + "/files").then(function(r) { return r.json(); }).then(function(files) {
            var html = "<ul>";
            files.forEach(function(f) { html += "<li>" + f.name + " (" + f.type + ")</li>"; });
            html += "</ul>"; div.innerHTML = html;
        });
        div.style.display = "block";
    } else div.style.display = "none";
}

// ===================== SETTINGS: Providers =====================
function loadProviders() {
    fetch("/api/providers").then(function(r) { return r.json(); }).then(function(d) {
        var html = "<ul>";
        d.forEach(function(p) {
            html += "<li>";
            if (p.active) html += "<b>🟢 " + p.name + " (active)</b>";
            else if (p.enabled) html += "✅ " + p.name;
            else html += "❌ " + p.name;
            html += " - " + p.model + " (priority:" + p.priority + ")</li>";
        });
        html += "</ul>"; document.getElementById("providers-list").innerHTML = html;
    });
}

// ===================== SETTINGS: Models =====================
var activeModelId = "";
function loadModels() {
    fetch("/api/providers").then(function(r) { return r.json(); }).then(function(providers) {
        var active = providers.find(function(p) { return p.active; });
        if (active) activeModelId = active.model; else activeModelId = "";
        fetch("/api/models").then(function(r2) { return r2.json(); }).then(function(models) {
            var html = "";
            if (Array.isArray(models) && models.length) {
                html += '<table class="backup-table"><thead><tr><th>Model ID</th><th>Description</th><th>Rate Limit</th><th>Action</th></tr></thead><tbody>';
                models.forEach(function(m) {
                    var isActive = (m.id === activeModelId);
                    var rowStyle = isActive ? 'style="background:#e6ffe6;"' : '';
                    html += '<tr ' + rowStyle + '><td>' + m.id + (isActive ? ' <b>(Active)</b>' : '') + '</td><td>' + m.description + '</td><td>';
                    if (!isActive) html += '<button onclick="selectModel(\'' + m.id + '\')">Select</button>';
                    else html += '<span style="color:green;">Currently Active</span>';
                    html += '</td></tr>';
                });
                html += '</tbody></table>';
            } else html = "<p>No models fetched.</p>";
            document.getElementById("models-list").innerHTML = html;
        });
    });
}
function selectModel(modelId) {
    if (!confirm("Change model to " + modelId + "? This will reload ARIA.")) return;
    fetch("/api/models/select", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model_id: modelId }) })
    .then(function(r) { return r.json(); }).then(function(d) {
        if (d.success) { alert("Model changed. Reloading..."); location.reload(); }
        else alert("Error: " + d.error);
    });
}

// ===================== SETTINGS: Memory =====================
function loadMemory() {
    fetch("/api/memory").then(function(r) { return r.json(); }).then(function(d) {
        var html = "<ul>";
        for (var k in d) html += '<li><b>' + k + ':</b> ' + d[k] + ' <button onclick="deleteMemory(\'' + k + '\')">Delete</button></li>';
        html += "</ul>"; document.getElementById("memory-list").innerHTML = html;
    });
}
function deleteMemory(key) { fetch("/api/memory/" + key, { method: "DELETE" }).then(function(r) { return r.json(); }).then(function() { loadMemory(); }); }

// ===================== SETTINGS: Backup =====================
var allBackups = [];
function backupNow() {
    var customName = document.getElementById("backup-custom-name").value.trim();
    fetch("/api/backup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ custom_name: customName || null }) })
    .then(function(r) { return r.json(); }).then(function(d) {
        if (d.success) { alert("✅ Backup created: " + d.filename + "\n\n" + d.diff); loadBackups(); }
        else alert("❌ Backup failed: " + d.error);
    });
}
function loadBackups() {
    fetch("/api/backups").then(function(r) { return r.json(); }).then(function(backups) {
        allBackups = backups; filterBackups();
    });
}
function filterBackups() {
    var searchTerm = document.getElementById("backup-search").value.trim().toLowerCase();
    var dateFrom = document.getElementById("backup-date-from").value, dateTo = document.getElementById("backup-date-to").value;
    var filtered = allBackups.filter(function(b) {
        if (searchTerm && !b.name.toLowerCase().includes(searchTerm)) return false;
        if (dateFrom || dateTo) {
            var bDate = new Date(b.date + "Z"); if (isNaN(bDate.getTime())) return true;
            if (dateFrom) { var fromDate = new Date(dateFrom + "T00:00:00Z"); if (bDate < fromDate) return false; }
            if (dateTo) { var toDate = new Date(dateTo + "T23:59:59Z"); if (bDate > toDate) return false; }
        }
        return true;
    });
    renderBackupTable(filtered);
}
function renderBackupTable(backups) {
    var countSpan = document.getElementById("backup-count");
    if (countSpan) countSpan.textContent = "Total backups: " + backups.length;
    var html = "";
    if (backups.length === 0) { html = "<p>No backups found matching your criteria.</p>"; }
    else {
        html += '<table class="backup-table"><thead><tr><th>Name</th><th>Size</th><th>Date</th><th>Actions</th></tr></thead><tbody>';
        backups.forEach(function(b) {
            html += '<tr><td><span id="display-' + b.name + '">' + b.name + '</span><input type="text" id="edit-' + b.name + '" value="' + b.name + '" style="display:none; width:150px;"></td>';
            html += '<td>' + b.size_kb + ' KB</td><td>' + b.date + '</td>';
            html += '<td>';
            html += '<button onclick="viewBackupDiff(\'' + b.name + '\')">📊 Diff</button> ';
            html += '<button onclick="restoreBackup(\'' + b.name + '\')">🔄 Restore</button> ';
            html += '<button onclick="deleteBackup(\'' + b.name + '\')">🗑 Delete</button> ';
            html += '<button onclick="startRename(\'' + b.name + '\')">✏️ Rename</button>';
            html += '<button onclick="saveRename(\'' + b.name + '\')" style="display:none;" id="save-' + b.name + '">💾 Save</button>';
            html += '</td></tr>';
        });
        html += '</tbody></table>';
    }
    document.getElementById("backup-list").innerHTML = html;
}
function clearBackupFilters() { document.getElementById("backup-search").value = ""; document.getElementById("backup-date-from").value = ""; document.getElementById("backup-date-to").value = ""; filterBackups(); }
function startRename(oldName) { document.getElementById("display-" + oldName).style.display = "none"; document.getElementById("edit-" + oldName).style.display = "inline-block"; document.getElementById("save-" + oldName).style.display = "inline-block"; }
function saveRename(oldName) {
    var newName = document.getElementById("edit-" + oldName).value.trim();
    if (!newName) { alert("Name cannot be empty"); return; }
    fetch("/api/backup/rename", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ old_name: oldName, new_name: newName }) })
    .then(function(r) { return r.json(); }).then(function(d) { if (d.success) loadBackups(); else alert("Rename failed: " + d.error); });
}
function viewBackupDiff(filename) { fetch("/api/backup_diff/" + filename).then(function(r) { return r.json(); }).then(function(d) { alert("Backup: " + filename + "\n\n" + (d.diff || "No diff available.")); }); }
function restoreBackup(filename) {
    if (!confirm("Restore " + filename + "? This will overwrite current data.")) return;
    fetch("/api/restore", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: filename }) })
    .then(function(r) { return r.json(); }).then(function(d) { if (d.success) { alert("Restored. Reloading..."); location.reload(); } else alert("Restore failed: " + d.error); });
}
function deleteBackup(filename) {
    if (!confirm("Delete backup " + filename + "?")) return;
    fetch("/api/backup/" + filename, { method: "DELETE" }).then(function(r) { return r.json(); }).then(function(d) { if (d.success) loadBackups(); else alert("Delete failed: " + d.error); });
}

// ===================== ANDROID =====================
function loadBattery() {
    fetch("/api/android/battery").then(function(r) { return r.json(); }).then(function(d) {
        if (d.error) { document.getElementById("battery-status").innerHTML = "Error: " + d.error; return; }
        document.getElementById("battery-status").innerHTML = "Level: " + d.percentage + "%<br>Status: " + d.status + "<br>Plugged: " + d.plugged + "<br>Temp: " + d.temperature + "°C<br>Health: " + d.health;
    });
}
function sendSms() {
    var num = document.getElementById("sms-number").value.trim(), txt = document.getElementById("sms-text").value.trim();
    if (!num || !txt) { alert("Fill number and message"); return; }
    fetch("/api/android/sms", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ number: num, text: txt }) })
    .then(function(r) { return r.json(); }).then(function(d) { document.getElementById("sms-result").innerHTML = d.success ? "✅ Sent" : "Error: " + d.error; });
}
function sendNotification() {
    var title = document.getElementById("notif-title").value.trim() || "ARIA", body = document.getElementById("notif-body").value.trim();
    if (!body) { alert("Enter body"); return; }
    fetch("/api/android/notify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: title, body: body }) })
    .then(function(r) { return r.json(); }).then(function(d) { document.getElementById("notif-result").innerHTML = d.success ? "✅ Sent" : "Error: " + d.error; });
}
function takePhoto() { document.getElementById("camera-result").innerHTML = "Taking photo..."; fetch("/api/android/camera", { method: "POST" }).then(function(r) { return r.json(); }).then(function(d) { document.getElementById("camera-result").innerHTML = d.success ? "✅ Saved to " + d.path : "Error: " + d.error; }); }
function loadWifiScan() { fetch("/api/android/wifi_scan").then(function(r) { return r.json(); }).then(function(d) { if (d.error) { document.getElementById("wifi-scan-list").innerHTML = "Error: " + d.error; return; } var html = ""; d.forEach(function(n) { html += n.ssid + " (" + n.strength + "dBm)<br>"; }); document.getElementById("wifi-scan-list").innerHTML = html || "No networks"; }); }
function loadWifiConnection() { fetch("/api/android/wifi_connection").then(function(r) { return r.json(); }).then(function(d) { if (d.error) { document.getElementById("wifi-connection-info").innerHTML = "Error: " + d.error; return; } document.getElementById("wifi-connection-info").innerHTML = "SSID: " + d.ssid + "<br>BSSID: " + d.bssid + "<br>IP: " + d.ip + "<br>Speed: " + d.link_speed + "Mbps"; }); }
function mediaControl(cmd) { fetch("/api/android/media", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: cmd }) }).then(function(r) { return r.json(); }).then(function(d) { document.getElementById("media-result").innerHTML = d.success ? "✅ " + cmd : "Error: " + d.error; }); }
function loadSmsInbox() { fetch("/api/android/sms_inbox").then(function(r) { return r.json(); }).then(function(d) { if (d.error) { document.getElementById("sms-inbox-list").innerHTML = "Error: " + d.error; return; } var html = ""; d.forEach(function(m) { html += m.number + " (" + m.date + "): " + m.body + "<br>"; }); document.getElementById("sms-inbox-list").innerHTML = html || "Empty"; }); }
function setAlarm() { var time = document.getElementById("alarm-time").value.trim(), title = document.getElementById("alarm-title").value.trim() || "Alarm"; if (!time) { alert("Enter epoch ms"); return; } fetch("/api/android/alarm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ time_ms: time, title: title }) }).then(function(r) { return r.json(); }).then(function(d) { document.getElementById("alarm-result").innerHTML = d.success ? "✅ Alarm set" : "Error: " + d.error; }); }
function scheduleNotify() { var time = document.getElementById("sched-time").value.trim(), msg = document.getElementById("sched-msg").value.trim(); if (!time || !msg) { alert("Enter time and message"); return; } fetch("/api/android/schedule_notify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ time: time, message: msg }) }).then(function(r) { return r.json(); }).then(function(d) { document.getElementById("sched-result").innerHTML = d.success ? "✅ Scheduled" : "Error: " + d.error; }); }
function loadLocation() { document.getElementById("location-info").innerHTML = "Getting location..."; fetch("/api/android/location").then(function(r) { return r.json(); }).then(function(d) { if (d.error) { document.getElementById("location-info").innerHTML = "Error: " + d.error; return; } document.getElementById("location-info").innerHTML = "Lat: " + d.latitude + "<br>Lon: " + d.longitude + "<br>Alt: " + (d.altitude || "N/A") + "m<br>Speed: " + (d.speed || "N/A") + "m/s"; }); }
function startListening() { var lang = document.getElementById("stt-lang").value; document.getElementById("stt-result").innerHTML = "🎤 Listening..."; fetch("/api/android/speech_to_text", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ lang: lang }) }).then(function(r) { return r.json(); }).then(function(d) { if (d.text) document.getElementById("stt-result").innerHTML = "You said: <b>" + d.text + "</b>"; else document.getElementById("stt-result").innerHTML = "Error: " + (d.error || "No speech recognized"); }); }
function speakText() { var text = document.getElementById("tts-text").value.trim(), lang = document.getElementById("tts-lang").value; if (!text) { alert("Enter text to speak"); return; } document.getElementById("tts-result").innerHTML = "🔊 Speaking..."; fetch("/api/android/text_to_speech", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: text, lang: lang }) }).then(function(r) { return r.json(); }).then(function(d) { if (d.success) document.getElementById("tts-result").innerHTML = "✅ Spoken"; else document.getElementById("tts-result").innerHTML = "Error: " + d.error; }); }

// ===================== PLUGINS =====================
function loadPlugins() {
    fetch("/api/plugins").then(function(r) { return r.json(); }).then(function(plugins) {
        var html = "";
        if (plugins.length === 0) html = "<p>No plugins installed.</p>";
        else {
            plugins.forEach(function(p) {
                html += '<div class="card"><b>' + p.name + '</b> v' + p.version + ' by ' + p.author;
                html += '<p>' + p.description + '</p>';
                html += '<label><input type="checkbox" onchange="togglePlugin(\'' + p.name + '\', this.checked)" ' + (p.enabled ? 'checked' : '') + '> ' + (p.enabled ? 'Enabled' : 'Disabled') + '</label>';
                html += '</div>';
            });
        }
        document.getElementById("plugins-list").innerHTML = html;
        loadWidgets();
    });
}
function togglePlugin(name, enabled) { fetch("/api/plugins/" + name + "/toggle", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled: enabled }) }).then(function(r) { return r.json(); }).then(function(d) { if (!d.success) { alert("Failed to toggle plugin."); loadPlugins(); } }); }
function loadWidgets() {
    fetch("/api/plugins/widgets").then(function(r) { return r.json(); }).then(function(widgets) {
        var container = document.getElementById("plugins-widgets"); if (!container) return; var html = "";
        if (widgets.length === 0) html = "<p>No plugin widgets available.</p>";
        else { widgets.forEach(function(w) { html += '<div class="card"><h4>⚡ ' + w.plugin + ' - ' + w.widget_name + '</h4>' + w.html + '</div>'; }); }
        container.innerHTML = html;
        if (document.getElementById('quran-type')) { initQuranWidget(); }
    });
}
function searchElectronicsWidget() {
    var part = document.getElementById('electronics-widget-input').value.trim();
    if (!part) { alert('Enter a part number.'); return; }
    var resultDiv = document.getElementById('electronics-widget-result'); resultDiv.innerHTML = 'Searching...';
    fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: 'electronics_parts tool use karke ' + part + ' ke baare mein batao' }) })
    .then(function(r) { return r.json(); }).then(function(d) { if (d.response) resultDiv.innerHTML = d.response; else resultDiv.innerHTML = '<p style="color:red;">Error: Unable to fetch data.</p>'; })
    .catch(function(e) { resultDiv.innerHTML = '<p style="color:red;">Network error.</p>'; });
}
function searchWeatherWidget() {
    var city = document.getElementById('weather-city-input').value.trim();
    if (!city) { alert('Enter a city name.'); return; }
    var resultDiv = document.getElementById('weather-widget-result'); resultDiv.innerHTML = 'Fetching weather...';
    fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: 'weather_tool tool use karke ' + city + ' ka mausam batao' }) })
    .then(function(r) { return r.json(); }).then(function(d) { if (d.response) resultDiv.innerHTML = d.response; else resultDiv.innerHTML = '<p style="color:red;">Error: Unable to fetch weather.</p>'; })
    .catch(function(e) { resultDiv.innerHTML = '<p style="color:red;">Network error.</p>'; });
}

// ===================== QURAN WIDGET =====================
var quranSurahs = [{"number": 1, "name_ar": "الفاتحة", "name_en": "Al-Fatihah"}, {"number": 2, "name_ar": "البقرة", "name_en": "Al-Baqarah"}, {"number": 3, "name_ar": "آل عمران", "name_en": "Aal-e-Imran"}, {"number": 4, "name_ar": "النساء", "name_en": "An-Nisa"}, {"number": 5, "name_ar": "المائدة", "name_en": "Al-Maidah"}, {"number": 6, "name_ar": "الأنعام", "name_en": "Al-An'am"}, {"number": 7, "name_ar": "الأعراف", "name_en": "Al-A'raf"}, {"number": 8, "name_ar": "الأنفال", "name_en": "Al-Anfal"}, {"number": 9, "name_ar": "التوبة", "name_en": "At-Tawbah"}, {"number": 10, "name_ar": "يونس", "name_en": "Yunus"}, {"number": 11, "name_ar": "هود", "name_en": "Hud"}, {"number": 12, "name_ar": "يوسف", "name_en": "Yusuf"}, {"number": 13, "name_ar": "الرعد", "name_en": "Ar-Ra'd"}, {"number": 14, "name_ar": "ابراهيم", "name_en": "Ibrahim"}, {"number": 15, "name_ar": "الحجر", "name_en": "Al-Hijr"}, {"number": 16, "name_ar": "النحل", "name_en": "An-Nahl"}, {"number": 17, "name_ar": "الإسراء", "name_en": "Al-Isra"}, {"number": 18, "name_ar": "الكهف", "name_en": "Al-Kahf"}, {"number": 19, "name_ar": "مريم", "name_en": "Maryam"}, {"number": 20, "name_ar": "طه", "name_en": "Ta-Ha"}, {"number": 21, "name_ar": "الأنبياء", "name_en": "Al-Anbiya"}, {"number": 22, "name_ar": "الحج", "name_en": "Al-Hajj"}, {"number": 23, "name_ar": "المؤمنون", "name_en": "Al-Mu'minun"}, {"number": 24, "name_ar": "النور", "name_en": "An-Nur"}, {"number": 25, "name_ar": "الفرقان", "name_en": "Al-Furqan"}, {"number": 26, "name_ar": "الشعراء", "name_en": "Ash-Shu'ara"}, {"number": 27, "name_ar": "النمل", "name_en": "An-Naml"}, {"number": 28, "name_ar": "القصص", "name_en": "Al-Qasas"}, {"number": 29, "name_ar": "العنكبوت", "name_en": "Al-Ankabut"}, {"number": 30, "name_ar": "الروم", "name_en": "Ar-Rum"}, {"number": 31, "name_ar": "لقمان", "name_en": "Luqman"}, {"number": 32, "name_ar": "السجدة", "name_en": "As-Sajdah"}, {"number": 33, "name_ar": "الأحزاب", "name_en": "Al-Ahzab"}, {"number": 34, "name_ar": "سبأ", "name_en": "Saba"}, {"number": 35, "name_ar": "فاطر", "name_en": "Fatir"}, {"number": 36, "name_ar": "يس", "name_en": "Ya-Sin"}, {"number": 37, "name_ar": "الصافات", "name_en": "As-Saffat"}, {"number": 38, "name_ar": "ص", "name_en": "Sad"}, {"number": 39, "name_ar": "الزمر", "name_en": "Az-Zumar"}, {"number": 40, "name_ar": "غافر", "name_en": "Ghafir"}, {"number": 41, "name_ar": "فصلت", "name_en": "Fussilat"}, {"number": 42, "name_ar": "الشورى", "name_en": "Ash-Shura"}, {"number": 43, "name_ar": "الزخرف", "name_en": "Az-Zukhruf"}, {"number": 44, "name_ar": "الدخان", "name_en": "Ad-Dukhan"}, {"number": 45, "name_ar": "الجاثية", "name_en": "Al-Jathiyah"}, {"number": 46, "name_ar": "الأحقاف", "name_en": "Al-Ahqaf"}, {"number": 47, "name_ar": "محمد", "name_en": "Muhammad"}, {"number": 48, "name_ar": "الفتح", "name_en": "Al-Fath"}, {"number": 49, "name_ar": "الحجرات", "name_en": "Al-Hujurat"}, {"number": 50, "name_ar": "ق", "name_en": "Qaf"}, {"number": 51, "name_ar": "الذاريات", "name_en": "Adh-Dhariyat"}, {"number": 52, "name_ar": "الطور", "name_en": "At-Tur"}, {"number": 53, "name_ar": "النجم", "name_en": "An-Najm"}, {"number": 54, "name_ar": "القمر", "name_en": "Al-Qamar"}, {"number": 55, "name_ar": "الرحمن", "name_en": "Ar-Rahman"}, {"number": 56, "name_ar": "الواقعة", "name_en": "Al-Waqi'ah"}, {"number": 57, "name_ar": "الحديد", "name_en": "Al-Hadid"}, {"number": 58, "name_ar": "المجادلة", "name_en": "Al-Mujadilah"}, {"number": 59, "name_ar": "الحشر", "name_en": "Al-Hashr"}, {"number": 60, "name_ar": "الممتحنة", "name_en": "Al-Mumtahinah"}, {"number": 61, "name_ar": "الصف", "name_en": "As-Saff"}, {"number": 62, "name_ar": "الجمعة", "name_en": "Al-Jumu'ah"}, {"number": 63, "name_ar": "المنافقون", "name_en": "Al-Munafiqun"}, {"number": 64, "name_ar": "التغابن", "name_en": "At-Taghabun"}, {"number": 65, "name_ar": "الطلاق", "name_en": "At-Talaq"}, {"number": 66, "name_ar": "التحريم", "name_en": "At-Tahrim"}, {"number": 67, "name_ar": "الملك", "name_en": "Al-Mulk"}, {"number": 68, "name_ar": "القلم", "name_en": "Al-Qalam"}, {"number": 69, "name_ar": "الحاقة", "name_en": "Al-Haqqah"}, {"number": 70, "name_ar": "المعارج", "name_en": "Al-Ma'arij"}, {"number": 71, "name_ar": "نوح", "name_en": "Nuh"}, {"number": 72, "name_ar": "الجن", "name_en": "Al-Jinn"}, {"number": 73, "name_ar": "المزمل", "name_en": "Al-Muzzammil"}, {"number": 74, "name_ar": "المدثر", "name_en": "Al-Muddaththir"}, {"number": 75, "name_ar": "القيامة", "name_en": "Al-Qiyamah"}, {"number": 76, "name_ar": "الإنسان", "name_en": "Al-Insan"}, {"number": 77, "name_ar": "المرسلات", "name_en": "Al-Mursalat"}, {"number": 78, "name_ar": "النبأ", "name_en": "An-Naba"}, {"number": 79, "name_ar": "النازعات", "name_en": "An-Nazi'at"}, {"number": 80, "name_ar": "عبس", "name_en": "Abasa"}, {"number": 81, "name_ar": "التكوير", "name_en": "At-Takwir"}, {"number": 82, "name_ar": "الإنفطار", "name_en": "Al-Infitar"}, {"number": 83, "name_ar": "المطففين", "name_en": "Al-Mutaffifin"}, {"number": 84, "name_ar": "الإنشقاق", "name_en": "Al-Inshiqaq"}, {"number": 85, "name_ar": "البروج", "name_en": "Al-Buruj"}, {"number": 86, "name_ar": "الطارق", "name_en": "At-Tariq"}, {"number": 87, "name_ar": "الأعلى", "name_en": "Al-A'la"}, {"number": 88, "name_ar": "الغاشية", "name_en": "Al-Ghashiyah"}, {"number": 89, "name_ar": "الفجر", "name_en": "Al-Fajr"}, {"number": 90, "name_ar": "البلد", "name_en": "Al-Balad"}, {"number": 91, "name_ar": "الشمس", "name_en": "Ash-Shams"}, {"number": 92, "name_ar": "الليل", "name_en": "Al-Layl"}, {"number": 93, "name_ar": "الضحى", "name_en": "Ad-Duha"}, {"number": 94, "name_ar": "الشرح", "name_en": "Ash-Sharh"}, {"number": 95, "name_ar": "التين", "name_en": "At-Tin"}, {"number": 96, "name_ar": "العلق", "name_en": "Al-Alaq"}, {"number": 97, "name_ar": "القدر", "name_en": "Al-Qadr"}, {"number": 98, "name_ar": "البينة", "name_en": "Al-Bayyinah"}, {"number": 99, "name_ar": "الزلزلة", "name_en": "Az-Zalzalah"}, {"number": 100, "name_ar": "العاديات", "name_en": "Al-Adiyat"}, {"number": 101, "name_ar": "القارعة", "name_en": "Al-Qari'ah"}, {"number": 102, "name_ar": "التكاثر", "name_en": "At-Takathur"}, {"number": 103, "name_ar": "العصر", "name_en": "Al-Asr"}, {"number": 104, "name_ar": "الهمزة", "name_en": "Al-Humazah"}, {"number": 105, "name_ar": "الفيل", "name_en": "Al-Fil"}, {"number": 106, "name_ar": "قريش", "name_en": "Quraysh"}, {"number": 107, "name_ar": "الماعون", "name_en": "Al-Ma'un"}, {"number": 108, "name_ar": "الكوثر", "name_en": "Al-Kawthar"}, {"number": 109, "name_ar": "الكافرون", "name_en": "Al-Kafirun"}, {"number": 110, "name_ar": "النصر", "name_en": "An-Nasr"}, {"number": 111, "name_ar": "المسد", "name_en": "Al-Masad"}, {"number": 112, "name_ar": "الإخلاص", "name_en": "Al-Ikhlas"}, {"number": 113, "name_ar": "الفلق", "name_en": "Al-Falaq"}, {"number": 114, "name_ar": "الناس", "name_en": "An-Nas"}];
var quranJuzs = [{"number": 1, "start": "1:1", "end": "2:141"}, {"number": 2, "start": "2:142", "end": "2:252"}, {"number": 3, "start": "2:253", "end": "3:92"}, {"number": 4, "start": "3:93", "end": "4:23"}, {"number": 5, "start": "4:24", "end": "4:147"}, {"number": 6, "start": "4:148", "end": "5:81"}, {"number": 7, "start": "5:82", "end": "6:110"}, {"number": 8, "start": "6:111", "end": "7:87"}, {"number": 9, "start": "7:88", "end": "8:40"}, {"number": 10, "start": "8:41", "end": "9:92"}, {"number": 11, "start": "9:93", "end": "11:5"}, {"number": 12, "start": "11:6", "end": "12:52"}, {"number": 13, "start": "12:53", "end": "14:52"}, {"number": 14, "start": "15:1", "end": "16:128"}, {"number": 15, "start": "17:1", "end": "18:74"}, {"number": 16, "start": "18:75", "end": "20:135"}, {"number": 17, "start": "21:1", "end": "22:78"}, {"number": 18, "start": "23:1", "end": "25:20"}, {"number": 19, "start": "25:21", "end": "27:55"}, {"number": 20, "start": "27:56", "end": "29:45"}, {"number": 21, "start": "29:46", "end": "33:30"}, {"number": 22, "start": "33:31", "end": "36:27"}, {"number": 23, "start": "36:28", "end": "39:31"}, {"number": 24, "start": "39:32", "end": "41:46"}, {"number": 25, "start": "41:47", "end": "45:37"}, {"number": 26, "start": "46:1", "end": "51:30"}, {"number": 27, "start": "51:31", "end": "57:29"}, {"number": 28, "start": "58:1", "end": "66:12"}, {"number": 29, "start": "67:1", "end": "77:50"}, {"number": 30, "start": "78:1", "end": "114:6"}];
var currentAyahs = [];

function toggleQuranType() {
    var type = document.getElementById('quran-type').value;
    if (type === 'surah') {
        populateQuranList('surah');
    } else {
        populateQuranList('juz');
    }
}

function fetchQuranSurahs() {
    fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: 'quran_hadith_tool tool use karke action quran_list_surahs' }) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        try { quranSurahs = JSON.parse(d.response); } catch(e) { quranSurahs = []; }
        populateQuranList('surah');
    });
}

function fetchQuranJuzs() {
    fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: 'quran_hadith_tool tool use karke action quran_list_juzs' }) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        try { quranJuzs = JSON.parse(d.response); } catch(e) { quranJuzs = []; }
        populateQuranList('juz');
    });
}

function populateQuranList(type) {
    var select = document.getElementById('quran-list');
    select.innerHTML = '';
    if (type === 'surah') {
        quranSurahs.forEach(function(s) {
            var opt = document.createElement('option');
            opt.value = s.number;
            opt.textContent = s.number + '. ' + s.name_en + ' (' + s.name_ar + ')';
            select.appendChild(opt);
        });
    } else {
        quranJuzs.forEach(function(j) {
            var opt = document.createElement('option');
            opt.value = j.number;
            opt.textContent = 'Juz ' + j.number + ' (' + j.start + ' - ' + j.end + ')';
            select.appendChild(opt);
        });
    }
}

function loadQuranAyahs() {
    var type = document.getElementById('quran-type').value;
    var value = document.getElementById('quran-list').value;
    var msg = type === 'surah' ? 'quran_hadith_tool tool use karke action quran_get_ayahs surah ' + value : 'quran_hadith_tool tool use karke action quran_get_juz juz ' + value;
    fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: msg }) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        try { currentAyahs = JSON.parse(d.response); } catch(e) { currentAyahs = []; }
        displayAyahs(currentAyahs);
    });
}

function displayAyahs(ayahs) {
    var div = document.getElementById('quran-ayahs');
    var html = '';
    ayahs.forEach(function(a) {
        html += '<div style="margin-bottom:15px; padding:10px; background:#fafafa; border:1px solid #eee; cursor:pointer;" onclick="showTafsir(\'' + a.number + '\')">';
        html += '<b>' + a.number + '</b>. ' + a.arabic;
        html += '<div style="color:#333; margin-top:5px;">🇵🇰 ' + a.urdu + '</div>';
        html += '<div style="color:#666;">🇬🇧 ' + a.en + '</div>';
        html += '</div>';
    });
    div.innerHTML = html;
    document.getElementById('quran-tafsir').style.display = 'none';
}

function showTafsir(num) {
    var parts = num.split(':');
    var surah = parts[0];
    var ayah = parts[1] || num;
    var msg = 'quran_hadith_tool tool use karke action quran_tafsir surah ' + surah + ' ayah ' + ayah;
    fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: msg }) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        var tafsirText = 'Tafsir not available.';
        try { tafsirText = JSON.parse(d.response).tafsir; } catch(e) {}
        var tafsirDiv = document.getElementById('quran-tafsir');
        tafsirDiv.innerHTML = '<h5>Tafsir (Jalalayn)</h5><p>' + tafsirText + '</p>';
        tafsirDiv.style.display = 'block';
    });
}


window.addEventListener('widgetsLoaded', function() {
    // Auto-populate Quran dropdown when widget DOM is ready
    setTimeout(function() {
        if (document.getElementById('quran-type')) {
            initQuranWidget();
        }
    }, 50);
});

function initQuranWidget() {
    // Direct call to fill the dropdown immediately
    if (document.getElementById('quran-type')) {
        initQuranWidget();
    }
}
    