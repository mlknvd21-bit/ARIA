// ===================== NAVIGATION =====================
function navigateTo(tabName, btn) {
    document.querySelectorAll('.tabcontent').forEach(function(c) { c.classList.remove('active'); });
    var target = document.getElementById(tabName);
    if (target) target.classList.add('active');
    document.querySelectorAll('.sidebar-link').forEach(function(b) { b.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    if (tabName === 'settings') { loadProviders(); loadModels(); loadMemory(); loadBackups(); }
    else if (tabName === 'projects') { loadProjects(); }
    else if (tabName === 'android') { loadBattery(); }
    else if (tabName === 'plugins') { loadPlugins(); }
}

function openTab(evt, tabName) {
    var btn = document.querySelector('.sidebar-link[onclick*="' + tabName + '"]');
    navigateTo(tabName, btn);
}

function toggleCollapse(id) {
    var el = document.getElementById(id);
    if (el.style.maxHeight && el.style.maxHeight !== "0px") {
        el.style.maxHeight = "0px"; el.style.padding = "0 20px";
    } else {
        el.style.maxHeight = el.scrollHeight + "px"; el.style.padding = "20px";
    }
}

// ===================== CHAT =====================
function sendMessage() {
    var input = document.getElementById("chat-input");
    var msg = input.value.trim();
    if (!msg) return;
    var box = document.getElementById("chat-box");
    var now = new Date();
    var timeStr = now.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    var msgId = 'msg-' + Date.now();

    box.innerHTML += '<div class="message-wrapper user slide-up" id="' + msgId + '">' +
        '<div class="avatar-small" style="background:#E1F5FE;color:#008080;border:1px solid #008080;">U</div>' +
        '<div class="bubble"><strong>You:</strong> ' + msg +
        '<div class="time">' + timeStr + '</div>' +
        '<div class="msg-actions"><button class="action-btn" onclick="copyMsg(\''+msgId+'\')"><i class="fas fa-copy"></i></button><button class="action-btn" onclick="forwardMsg(\''+msgId+'\')"><i class="fas fa-share"></i></button></div>' +
        '</div></div>';

    input.value = "";

    fetch("/api/chat", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})})
    .then(function(r){return r.json();}).then(function(d){
        var respText = d.response || d.error || "Error";
        var now2 = new Date();
        var timeStr2 = now2.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
        var ariaMsgId = 'msg-' + Date.now();
        box.innerHTML += '<div class="message-wrapper aria slide-up" id="' + ariaMsgId + '">' +
            '<div class="avatar-small">A</div>' +
            '<div class="bubble"><strong>ARIA:</strong> ' + respText +
            '<div class="time">' + timeStr2 + '</div>' +
            '<div class="msg-actions"><button class="action-btn like-btn" onclick="reactMsg(\''+ariaMsgId+'\',\'like\')"><i class="far fa-thumbs-up"></i></button><button class="action-btn dislike-btn" onclick="reactMsg(\''+ariaMsgId+'\',\'dislike\')"><i class="far fa-thumbs-down"></i></button><button class="action-btn" onclick="copyMsg(\''+ariaMsgId+'\')"><i class="fas fa-copy"></i></button><button class="action-btn" onclick="forwardMsg(\''+ariaMsgId+'\')"><i class="fas fa-share"></i></button></div>' +
            '</div></div>';
        box.scrollTop = box.scrollHeight;
    }).catch(function(e){
        box.innerHTML += '<div class="message-wrapper aria slide-up"><div class="avatar-small">A</div><div class="bubble"><strong>ARIA:</strong> Network error</div></div>';
    });
}

function copyMsg(msgId) {
    var el = document.getElementById(msgId); if(!el)return;
    var text = el.querySelector('.bubble').textContent.replace(/You:|ARIA:/,'').replace(/\n/g,' ').trim();
    navigator.clipboard.writeText(text).then(function(){alert('Copied!');}).catch(function(){prompt('Copy:',text);});
}
function forwardMsg(msgId) {
    var el = document.getElementById(msgId); if(!el)return;
    var text = el.querySelector('.bubble').textContent.replace(/You:|ARIA:/,'').replace(/\n/g,' ').trim();
    navigator.clipboard.writeText(text).then(function(){alert('Copied for sharing!');}).catch(function(){prompt('Share:',text);});
}
function reactMsg(msgId, type) {
    var el = document.getElementById(msgId); if(!el)return;
    var likeBtn = el.querySelector('.like-btn'), dislikeBtn = el.querySelector('.dislike-btn');
    if(type==='like') {
        if(likeBtn.classList.contains('liked')) { likeBtn.classList.remove('liked'); } else { likeBtn.classList.add('liked'); if(dislikeBtn)dislikeBtn.classList.remove('disliked'); }
    } else if(type==='dislike') {
        if(dislikeBtn.classList.contains('disliked')) { dislikeBtn.classList.remove('disliked'); } else { dislikeBtn.classList.add('disliked'); if(likeBtn)likeBtn.classList.remove('liked'); }
    }
}

// ===================== SWARM =====================
function runSwarm() {
    var task = document.getElementById("swarm-input").value.trim();
    if(!task) { alert("Enter a task"); return; }
    var res = document.getElementById("swarm-result");
    res.textContent = "Running Swarm...";
    fetch("/api/swarm", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task:task})})
    .then(function(r){return r.json();}).then(function(d){res.textContent = d.result || d.error || "No response";});
}

// ===================== PROJECTS =====================
function loadProjects() { fetch("/api/projects").then(function(r){return r.json();}).then(function(data){var html="";if(Array.isArray(data)&&data.length){data.forEach(function(p){html+='<div class="card"><b>'+p.name+'</b> (web:'+(p.has_web?"Yes":"No")+')';if(p.running)html+=' 🔵 Running on port '+p.port+' <button onclick="stopProject(\''+p.name+'\')">Stop</button>';html+='<br><button onclick="runProject(\''+p.name+'\')">Run</button> <button onclick="toggleFiles(\''+p.name+'\')">Files</button>';html+='<div id="files-'+p.name+'" style="display:none;margin-top:5px;"></div></div>';});}else html="<p>No projects yet.</p>";document.getElementById("projects-list").innerHTML = html;});}
function runProject(name){fetch("/api/projects/"+name+"/run",{method:"POST"}).then(function(r){return r.json();}).then(function(d){if(d.url)window.open(d.url,"_blank");else alert("Error");});}
function stopProject(name){fetch("/api/projects/"+name+"/stop",{method:"POST"}).then(function(r){return r.json();}).then(function(){loadProjects();});}
function toggleFiles(name){var div = document.getElementById("files-"+name);if(div.style.display==="none"||div.style.display===""){fetch("/api/projects/"+name+"/files").then(function(r){return r.json();}).then(function(files){var html="<ul>";files.forEach(function(f){html+="<li>"+f.name+" ("+f.type+")</li>";});html+="</ul>";div.innerHTML=html;});div.style.display="block";}else div.style.display="none";}

// ===================== SETTINGS =====================
function loadProviders() { fetch("/api/providers").then(function(r){return r.json();}).then(function(d){var html="<ul>";d.forEach(function(p){html+="<li>";if(p.active)html+="<b>🟢 "+p.name+" (active)</b>";else if(p.enabled)html+="✅ "+p.name;else html+="❌ "+p.name;html+=" - "+p.model+" (priority:"+p.priority+")</li>";});html+="</ul>";document.getElementById("providers-list").innerHTML=html;});}
function loadModels() { fetch("/api/providers").then(function(r){return r.json();}).then(function(providers){var active=providers.find(function(p){return p.active;});var activeModelId=active?active.model:"";fetch("/api/models").then(function(r2){return r2.json();}).then(function(models){var html="";if(Array.isArray(models)&&models.length){html+='<table class="backup-table"><thead><tr><th>Model ID</th><th>Description</th><th>Action</th></tr></thead><tbody>';models.forEach(function(m){var isActive=(m.id===activeModelId);var rowStyle=isActive?'style="background:#e6ffe6;"':'';html+='<tr '+rowStyle+'><td>'+m.id+(isActive?' <b>(Active)</b>':'')+'</td><td>'+m.description+'</td><td>';if(!isActive)html+='<button onclick="selectModel(\''+m.id+'\')">Select</button>';else html+='<span style="color:green;">Currently Active</span>';html+='</td></tr>';});html+='</tbody></table>';}else html="<p>No models fetched.</p>";document.getElementById("models-list").innerHTML=html;});});}
function selectModel(modelId){if(!confirm("Change model to "+modelId+"?"))return;fetch("/api/models/select",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model_id:modelId})}).then(function(r){return r.json();}).then(function(d){if(d.success){alert("Model changed. Reloading...");location.reload();}else alert("Error: "+d.error);});}
function loadMemory() { fetch("/api/memory").then(function(r){return r.json();}).then(function(d){var html="<ul>";for(var k in d)html+='<li><b>'+k+':</b> '+d[k]+' <button onclick="deleteMemory(\''+k+'\')">Delete</button></li>';html+="</ul>";document.getElementById("memory-list").innerHTML=html;});}
function deleteMemory(key){fetch("/api/memory/"+key,{method:"DELETE"}).then(function(r){return r.json();}).then(function(){loadMemory();});}

// ===================== BACKUP =====================
var allBackups=[];
function backupNow(){var customName=document.getElementById("backup-custom-name").value.trim();fetch("/api/backup",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({custom_name:customName||null})}).then(function(r){return r.json();}).then(function(d){if(d.success){alert("✅ Backup created: "+d.filename+"\n\n"+d.diff);loadBackups();}else alert("❌ Backup failed: "+d.error);});}
function loadBackups(){fetch("/api/backups").then(function(r){return r.json();}).then(function(backups){allBackups=backups;filterBackups();});}
function filterBackups(){var searchTerm=document.getElementById("backup-search").value.trim().toLowerCase(),dateFrom=document.getElementById("backup-date-from").value,dateTo=document.getElementById("backup-date-to").value;var filtered=allBackups.filter(function(b){if(searchTerm&&!b.name.toLowerCase().includes(searchTerm))return false;if(dateFrom||dateTo){var bDate=new Date(b.date+"Z");if(isNaN(bDate.getTime()))return true;if(dateFrom){var fromDate=new Date(dateFrom+"T00:00:00Z");if(bDate<fromDate)return false;}if(dateTo){var toDate=new Date(dateTo+"T23:59:59Z");if(bDate>toDate)return false;}}return true;});renderBackupTable(filtered);}
function renderBackupTable(backups){var countSpan=document.getElementById("backup-count");if(countSpan)countSpan.textContent="Total backups: "+backups.length;var html="";if(backups.length===0)html="<p>No backups found matching your criteria.</p>";else{html+='<table class="backup-table"><thead><tr><th>Name</th><th>Size</th><th>Date</th><th>Actions</th></tr></thead><tbody>';backups.forEach(function(b){html+='<tr><td><span id="display-'+b.name+'">'+b.name+'</span><input type="text" id="edit-'+b.name+'" value="'+b.name+'" style="display:none;width:150px;"></td><td>'+b.size_kb+' KB</td><td>'+b.date+'</td><td>';html+='<button onclick="viewBackupDiff(\''+b.name+'\')">📊 Diff</button> <button onclick="restoreBackup(\''+b.name+'\')">🔄 Restore</button> <button onclick="deleteBackup(\''+b.name+'\')">🗑 Delete</button> <button onclick="startRename(\''+b.name+'\')">✏️ Rename</button><button onclick="saveRename(\''+b.name+'\')" style="display:none;" id="save-'+b.name+'">💾 Save</button>';html+='</td></tr>';});html+='</tbody></table>';}document.getElementById("backup-list").innerHTML=html;}
function clearBackupFilters(){document.getElementById("backup-search").value="";document.getElementById("backup-date-from").value="";document.getElementById("backup-date-to").value="";filterBackups();}
function startRename(oldName){document.getElementById("display-"+oldName).style.display="none";document.getElementById("edit-"+oldName).style.display="inline-block";document.getElementById("save-"+oldName).style.display="inline-block";}
function saveRename(oldName){var newName=document.getElementById("edit-"+oldName).value.trim();if(!newName){alert("Name cannot be empty");return;}fetch("/api/backup/rename",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({old_name:oldName,new_name:newName})}).then(function(r){return r.json();}).then(function(d){if(d.success)loadBackups();else alert("Rename failed: "+d.error);});}
function viewBackupDiff(filename){fetch("/api/backup_diff/"+filename).then(function(r){return r.json();}).then(function(d){alert("Backup: "+filename+"\n\n"+(d.diff||"No diff available."));});}
function restoreBackup(filename){if(!confirm("Restore "+filename+"? This will overwrite current data."))return;fetch("/api/restore",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename:filename})}).then(function(r){return r.json();}).then(function(d){if(d.success){alert("Restored. Reloading...");location.reload();}else alert("Restore failed: "+d.error);});}
function deleteBackup(filename){if(!confirm("Delete backup "+filename+"?"))return;fetch("/api/backup/"+filename,{method:"DELETE"}).then(function(r){return r.json();}).then(function(d){if(d.success)loadBackups();else alert("Delete failed: "+d.error);});}

// ===================== ANDROID =====================
function loadBattery(){fetch("/api/android/battery").then(function(r){return r.json();}).then(function(d){if(d.error){document.getElementById("battery-status").innerHTML="Error: "+d.error;return;}document.getElementById("battery-status").innerHTML="Level: "+d.percentage+"%<br>Status: "+d.status+"<br>Plugged: "+d.plugged+"<br>Temp: "+d.temperature+"°C<br>Health: "+d.health;});}
function sendSms(){var num=document.getElementById("sms-number").value.trim(),txt=document.getElementById("sms-text").value.trim();if(!num||!txt){alert("Fill number and message");return;}fetch("/api/android/sms",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({number:num,text:txt})}).then(function(r){return r.json();}).then(function(d){document.getElementById("sms-result").innerHTML=d.success?"✅ Sent":"Error: "+d.error;});}
function sendNotification(){var title=document.getElementById("notif-title").value.trim()||"ARIA",body=document.getElementById("notif-body").value.trim();if(!body){alert("Enter body");return;}fetch("/api/android/notify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:title,body:body})}).then(function(r){return r.json();}).then(function(d){document.getElementById("notif-result").innerHTML=d.success?"✅ Sent":"Error: "+d.error;});}
function takePhoto(){document.getElementById("camera-result").innerHTML="Taking photo...";fetch("/api/android/camera",{method:"POST"}).then(function(r){return r.json();}).then(function(d){document.getElementById("camera-result").innerHTML=d.success?"✅ Saved to "+d.path:"Error: "+d.error;});}
function loadWifiScan(){fetch("/api/android/wifi_scan").then(function(r){return r.json();}).then(function(d){if(d.error){document.getElementById("wifi-scan-list").innerHTML="Error: "+d.error;return;}var html="";d.forEach(function(n){html+=n.ssid+" ("+n.strength+"dBm)<br>";});document.getElementById("wifi-scan-list").innerHTML=html||"No networks";});}
function loadWifiConnection(){fetch("/api/android/wifi_connection").then(function(r){return r.json();}).then(function(d){if(d.error){document.getElementById("wifi-connection-info").innerHTML="Error: "+d.error;return;}document.getElementById("wifi-connection-info").innerHTML="SSID: "+d.ssid+"<br>BSSID: "+d.bssid+"<br>IP: "+d.ip+"<br>Speed: "+d.link_speed+"Mbps";});}
function mediaControl(cmd){fetch("/api/android/media",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({command:cmd})}).then(function(r){return r.json();}).then(function(d){document.getElementById("media-result").innerHTML=d.success?"✅ "+cmd:"Error: "+d.error;});}
function loadSmsInbox(){fetch("/api/android/sms_inbox").then(function(r){return r.json();}).then(function(d){if(d.error){document.getElementById("sms-inbox-list").innerHTML="Error: "+d.error;return;}var html="";d.forEach(function(m){html+=m.number+" ("+m.date+"): "+m.body+"<br>";});document.getElementById("sms-inbox-list").innerHTML=html||"Empty";});}
function setAlarm(){var time=document.getElementById("alarm-time").value.trim(),title=document.getElementById("alarm-title").value.trim()||"Alarm";if(!time){alert("Enter epoch ms");return;}fetch("/api/android/alarm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({time_ms:time,title:title})}).then(function(r){return r.json();}).then(function(d){document.getElementById("alarm-result").innerHTML=d.success?"✅ Alarm set":"Error: "+d.error;});}
function scheduleNotify(){var time=document.getElementById("sched-time").value.trim(),msg=document.getElementById("sched-msg").value.trim();if(!time||!msg){alert("Enter time and message");return;}fetch("/api/android/schedule_notify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({time:time,message:msg})}).then(function(r){return r.json();}).then(function(d){document.getElementById("sched-result").innerHTML=d.success?"✅ Scheduled":"Error: "+d.error;});}
function loadLocation(){document.getElementById("location-info").innerHTML="Getting location...";fetch("/api/android/location").then(function(r){return r.json();}).then(function(d){if(d.error){document.getElementById("location-info").innerHTML="Error: "+d.error;return;}document.getElementById("location-info").innerHTML="Lat: "+d.latitude+"<br>Lon: "+d.longitude+"<br>Alt: "+(d.altitude||"N/A")+"m<br>Speed: "+(d.speed||"N/A")+"m/s";});}
function startListening(){var lang=document.getElementById("stt-lang").value;document.getElementById("stt-result").innerHTML="🎤 Listening...";fetch("/api/android/speech_to_text",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({lang:lang})}).then(function(r){return r.json();}).then(function(d){if(d.text)document.getElementById("stt-result").innerHTML="You said: <b>"+d.text+"</b>";else document.getElementById("stt-result").innerHTML="Error: "+(d.error||"No speech recognized");});}
function speakText(){var text=document.getElementById("tts-text").value.trim(),lang=document.getElementById("tts-lang").value;if(!text){alert("Enter text to speak");return;}document.getElementById("tts-result").innerHTML="🔊 Speaking...";fetch("/api/android/text_to_speech",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:text,lang:lang})}).then(function(r){return r.json();}).then(function(d){if(d.success)document.getElementById("tts-result").innerHTML="✅ Spoken";else document.getElementById("tts-result").innerHTML="Error: "+d.error;});}

// ===================== PLUGINS =====================
function loadPlugins(){fetch("/api/plugins").then(function(r){return r.json();}).then(function(plugins){var html="";if(plugins.length===0)html="<p>No plugins installed.</p>";else{plugins.forEach(function(p){html+='<div class="card"><b>'+p.name+'</b> v'+p.version+' by '+p.author;html+='<p>'+p.description+'</p>';html+='<label><input type="checkbox" onchange="togglePlugin(\''+p.name+'\',this.checked)" '+(p.enabled?'checked':'')+'> '+(p.enabled?'Enabled':'Disabled')+'</label>';html+='</div>';});}document.getElementById("plugins-list").innerHTML=html;loadWidgets();});}
function togglePlugin(name,enabled){fetch("/api/plugins/"+name+"/toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({enabled:enabled})}).then(function(r){return r.json();}).then(function(d){if(!d.success){alert("Failed to toggle plugin.");loadPlugins();}});}
function loadWidgets(){fetch("/api/plugins/widgets").then(function(r){return r.json();}).then(function(widgets){var container=document.getElementById("plugins-widgets");if(!container)return;var html="";if(widgets.length===0)html="<p>No plugin widgets available.</p>";else{widgets.forEach(function(w){html+='<div class="card"><h4>⚡ '+w.plugin+' - '+w.widget_name+'</h4>'+w.html+'</div>';});}container.innerHTML=html;});}
function searchElectronicsWidget(){var part=document.getElementById('electronics-widget-input').value.trim();if(!part){alert('Enter a part number.');return;}var resultDiv=document.getElementById('electronics-widget-result');resultDiv.innerHTML='Searching...';fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'electronics_parts tool use karke '+part+' ke baare mein batao'})}).then(function(r){return r.json();}).then(function(d){if(d.response)resultDiv.innerHTML=d.response;else resultDiv.innerHTML='<p style="color:red;">Error: Unable to fetch data.</p>';}).catch(function(e){resultDiv.innerHTML='<p style="color:red;">Network error.</p>';});}
function searchWeatherWidget(){var city=document.getElementById('weather-city-input').value.trim();if(!city){alert('Enter a city name.');return;}var resultDiv=document.getElementById('weather-widget-result');resultDiv.innerHTML='Fetching weather...';fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'weather_tool tool use karke '+city+' ka mausam batao'})}).then(function(r){return r.json();}).then(function(d){if(d.response)resultDiv.innerHTML=d.response;else resultDiv.innerHTML='<p style="color:red;">Error: Unable to fetch weather.</p>';}).catch(function(e){resultDiv.innerHTML='<p style="color:red;">Network error.</p>';});}

// ===================== QURAN WIDGET =====================
var quranSurahs=[],quranJuzs=[],currentAyahs=[];
function toggleQuranType(){var type=document.getElementById('quran-type').value;if(type==='surah'){populateQuranList('surah');}else{populateQuranList('juz');}}
function fetchQuranSurahs(){populateQuranList('surah');}
function fetchQuranJuzs(){populateQuranList('juz');}
function populateQuranList(type){var select=document.getElementById('quran-list');select.innerHTML='';if(type==='surah'){quranSurahs.forEach(function(s){var opt=document.createElement('option');opt.value=s.number;opt.textContent=s.number+'. '+s.name_en+' ('+s.name_ar+')';select.appendChild(opt);});}else{quranJuzs.forEach(function(j){var opt=document.createElement('option');opt.value=j.number;opt.textContent='Juz '+j.number+' ('+j.start+' - '+j.end+')';select.appendChild(opt);});}}
function loadQuranAyahs(){var type=document.getElementById('quran-type').value,val=document.getElementById('quran-list').value;var msg=type==='surah'?'quran_hadith_tool tool use karke action quran_get_ayahs surah '+val:'quran_hadith_tool tool use karke action quran_get_juz juz '+val;fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})}).then(function(r){return r.json();}).then(function(d){try{currentAyahs=JSON.parse(d.response);}catch(e){currentAyahs=[];}displayAyahs(currentAyahs);});}
function displayAyahs(ayahs){var div=document.getElementById('quran-ayahs');var html='';ayahs.forEach(function(a){html+='<div style="margin-bottom:15px;padding:10px;background:#fafafa;border:1px solid #eee;cursor:pointer;" onclick="showTafsir(\''+a.number+'\')"><b>'+a.number+'</b>. '+a.arabic+'<div style="color:#333;margin-top:5px;">🇵🇰 '+a.urdu+'</div><div style="color:#666;">🇬🇧 '+a.en+'</div></div>';});div.innerHTML=html;document.getElementById('quran-tafsir').style.display='none';}
function showTafsir(num){var parts=num.split(':');var surah=parts[0];var ayah=parts[1]||num;var msg='quran_hadith_tool tool use karke action quran_tafsir surah '+surah+' ayah '+ayah;fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})}).then(function(r){return r.json();}).then(function(d){var tafsirText='Tafsir not available.';try{tafsirText=JSON.parse(d.response).tafsir;}catch(e){}var tafsirDiv=document.getElementById('quran-tafsir');tafsirDiv.innerHTML='<h5>Tafsir (Jalalayn)</h5><p>'+tafsirText+'</p>';tafsirDiv.style.display='block';});}

// ===================== HADITH WIDGET =====================
var hadithBooks=[];
function loadHadithBooks(){fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'quran_hadith_tool tool use karke action hadith sub_action list_books'})}).then(function(r){return r.json();}).then(function(d){try{hadithBooks=JSON.parse(d.response);}catch(e){hadithBooks=[];}var select=document.getElementById('hadith-book');select.innerHTML='';hadithBooks.forEach(function(b){var opt=document.createElement('option');opt.value=b.slug;opt.textContent=b.name+' ('+b.total+' hadiths)';select.appendChild(opt);});});}
function loadHadith(){var book=document.getElementById('hadith-book').value;var number=document.getElementById('hadith-number').value.trim();if(!book||!number){alert('Select a book and enter a hadith number.');return;}var resultDiv=document.getElementById('hadith-result');resultDiv.innerHTML='Loading...';fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'quran_hadith_tool tool use karke action hadith sub_action get_hadith book '+book+' number '+number})}).then(function(r){return r.json();}).then(function(d){try{var h=JSON.parse(d.response);if(h.error){resultDiv.innerHTML='<p style="color:red;">'+h.error+'</p>';}else{var gradeColor={'صحیح':'🟢','حسن':'🟡','ضعیف':'🔴'};var gradeIcon=gradeColor[h.grade]||'⚪';resultDiv.innerHTML='<div style="margin-bottom:15px;padding:10px;background:#fafafa;border:1px solid #eee;"><b>'+h.number+'</b>. '+h.arabic+'<div style="color:#333;margin-top:5px;">🇵🇰 '+h.urdu+'</div><div style="color:#666;">🇬🇧 '+h.english+'</div><div style="margin-top:5px;">'+gradeIcon+' '+h.grade+'</div></div>';}}catch(e){resultDiv.innerHTML='<p style="color:red;">Invalid response.</p>';}});}

// ===================== DEBUGGER (4 cards) =====================
function scanBugs() { fetchAndDisplay('/api/bugs/scan', 'Scanning static code...', '🔍'); }
function scanRuntime() { fetchAndDisplay('/api/bugs/runtime', 'Scanning server logs...', '📊'); }
function scanMissingFiles() { fetchAndDisplay('/api/bugs/missing-files', 'Searching for missing files...', '📁'); }
function scanStatusSummary() { fetchAndDisplay('/api/bugs/status-summary', 'Calculating status summary...', '📈'); }

function fetchAndDisplay(url, loadingText, icon) {
    var resDiv = document.getElementById('bugs-result');
    resDiv.innerHTML = '<div style="text-align:center;padding:30px;"><i class="fas fa-spinner fa-pulse" style="font-size:24px;color:#008080;"></i><p style="color:#aaa;">' + loadingText + '</p></div>';
    fetch(url)
    .then(function(r) { return r.json(); })
    .then(function(d) {
        var text = d.result || 'No response';
        if (text.startsWith('✅') || text.startsWith('ℹ️')) {
            resDiv.innerHTML = '<div class="card" style="padding:20px; text-align:center; color:#212121;">' + icon + ' ' + text + '</div>';
        } else {
            var lines = text.split('\\n');
            var html = '<div class="card" style="padding:20px; background:#1E1E1E; color:#D4D4D4; max-height:500px; overflow-y:auto; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.3);">';
            html += '<button onclick="copyBugResults()" style="float:right; background:#008080; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; margin-bottom:10px;"><i class="fas fa-copy"></i> Copy</button>';
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if (line.startsWith('🔍') || line.startsWith('📊')) html += '<div style="color:#4FC3F7; font-size:18px; margin-bottom:10px;">' + line + '</div>';
                else if (line.startsWith('---')) html += '<div style="color:#FFD54F; margin-top:10px;">' + line + '</div>';
                else if (line.startsWith('Status:') || line.startsWith('Path:') || line.startsWith('Occurrences:')) html += '<div style="margin-left:20px;">' + line + '</div>';
                else if (line.startsWith('🟢') || line.startsWith('🔵') || line.startsWith('🟡') || line.startsWith('🔴') || line.startsWith('⚪')) html += '<div style="margin-left:20px; font-size:15px;">' + line + '</div>';
                else if (line.includes('Error')) html += '<div style="color:#EF5350; margin-left:20px;">' + line + '</div>';
                else html += '<div>' + line + '</div>';
            }
            html += '</div>';
            resDiv.innerHTML = html;
        }
        window._bugResults = text;
    })
    .catch(function(e) { resDiv.innerHTML = '<p style="color:red;">⚠️ Network error.</p>'; });
}

function copyBugResults() {
    var text = window._bugResults || '';
    navigator.clipboard.writeText(text).then(function() { alert('✅ Copied!'); }).catch(function() { prompt('Copy:', text); });
}

// ===================== INIT =====================
document.addEventListener('DOMContentLoaded', function() {
    var chatBtn = document.querySelector('.sidebar-link[onclick*="chat"]');
    if (chatBtn) navigateTo('chat', chatBtn);
});
