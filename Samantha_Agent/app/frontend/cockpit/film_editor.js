(() => {
  "use strict";
  function create(root, options = {}) {
    const doc = options.document || document;
    const request = options.fetch || ((...args) => fetch(...args));
    const uuid = options.uuid || (() => {
      if (crypto.randomUUID) return crypto.randomUUID();
      const bytes = crypto.getRandomValues(new Uint8Array(16));
      bytes[6] = bytes[6] & 15 | 64; bytes[8] = bytes[8] & 63 | 128;
      const hex = [...bytes].map(b => b.toString(16).padStart(2, "0")).join("");
      return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
    });
    const later = options.setTimeout || setTimeout;
    const cancel = options.clearTimeout || clearTimeout;
    const askDelete = options.prompt || (message => window.prompt(message));
    const nodes = Object.fromEntries(["status", "shots", "voices", "jobs", "save", "preview", "final",
      "range", "from", "to", "duck", "player", "reload", "source", "sourcePlayer", "sourceStatus",
      "sourceTitle", "selection", "start", "end", "playSelection", "texts", "cards"].map(key => [key, root.querySelector(`[data-film="${key}"]`)]));
    let model = null, active = false, dirty = false, saving = false, version = 0, epoch = 0;
    let pending = null, timer = null, refreshTimer = null, preserved = null, readRequest = 0;
    let requestedProject = null, photoOpen = null, narrating = false;
    let photoStatuses = [], photoAudios = [], photoPanels = new Map();
    let deleting = false, deleteButtons = [];
    let selected = null, sourceJob = null, sourceRequest = 0, sourceTimer = null, selectionTimer = null, playingSelection = false;
    function text(tag, value) { const n = doc.createElement(tag); n.textContent = value; return n; }
    function stopPlayer() { nodes.player.pause(); nodes.player.removeAttribute("src"); nodes.player.load(); }
    function stopSource() {
      ++sourceRequest; cancel(sourceTimer); cancel(selectionTimer); selected = null; sourceJob = null; playingSelection = false;
      nodes.sourcePlayer.pause(); nodes.sourcePlayer.removeAttribute("src"); nodes.sourcePlayer.load();
      nodes.source.classList.add("hidden");
      for (const key of ["start", "end", "playSelection"]) nodes[key].disabled = true;
    }
    function selectedRow() { return model && [...model.draft.shots, ...model.draft.voices].find(row => row.asset_id === selected); }
    function safeOutput(url) {
      return typeof url === "string" && url.startsWith(`/api/camino/film/output/${model.project_id}/`)
        && url.split("/").length === 7 && /^[a-f0-9-]{36}$/.test(url.split("/")[6]);
    }
    function syncSelection() {
      const row = selectedRow(); if (!row) return;
      const source = model.sources.find(s => s.asset_id === selected);
      nodes.sourceTitle.textContent = `${source.kind === "audio" ? "Komentář" : "Video"} · ${source.title || "Bez názvu"}`;
      nodes.selection.textContent = `Vybraný úsek: ${(row.in_ms / 1000).toFixed(3)}–${(row.out_ms / 1000).toFixed(3)} s · ${((row.out_ms - row.in_ms) / 1000).toFixed(3)} s${row.included ? "" : " · vyřazeno z filmu"}`;
      const ready = !!nodes.sourcePlayer.getAttribute("src") && nodes.sourcePlayer.readyState >= 1;
      nodes.start.disabled = nodes.end.disabled = !ready;
      nodes.playSelection.disabled = !ready || row.in_ms < 0 || row.out_ms > source.duration_ms || row.out_ms <= row.in_ms;
    }
    function updateSource(jobs) {
      cancel(sourceTimer);
      if (!selected || !sourceJob) return;
      const job = jobs.find(j => j.job_id === sourceJob && j.source_asset_id === selected);
      if (!job) return;
      if (job.state === "ready" && safeOutput(job.url)) {
        if (nodes.sourcePlayer.getAttribute("src") !== job.url) {
          nodes.sourcePlayer.src = job.url; nodes.sourcePlayer.load();
        }
        nodes.sourceStatus.textContent = "Posuň přehrávač na požadované místo a označ začátek nebo konec. Přehrát výběr přehraje jen označenou část.";
      } else if (["failed", "interrupted"].includes(job.state)) {
        nodes.sourceStatus.textContent = "Náhled se nedokončil. Tlačítkem u záběru ho můžeš připravit znovu.";
      } else {
        nodes.sourceStatus.textContent = `Připravuji zdroj k přehrání${job.state === "rendering" ? ` · ${job.progress} %` : " · ve frontě"}…`;
        sourceTimer = later(() => check(), 1500);
      }
      syncSelection();
    }
    async function selectVideo(assetId) {
      if (!model) return;
      stopSource(); stopPlayer(); selected = assetId;
      const current = epoch, selection = sourceRequest;
      if (model.sources.find(s => s.asset_id === assetId)?.kind === "audio") nodes.source.classList.add("audio-only");
      else nodes.source.classList.remove("audio-only");
      nodes.source.classList.remove("hidden"); syncSelection();
      nodes.sourceStatus.textContent = "Ověřuji a připravuji celý zdroj k přehrání…";
      nodes.source.scrollIntoView?.({block: "nearest", behavior: "smooth"});
      try {
        const response = await request("/api/camino/film/source", {method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({project_id: model.project_id, asset_id: assetId, request_id: uuid()})});
        const data = await response.json();
        if (current !== epoch || selection !== sourceRequest || !active || doc.hidden) return;
        if (!data.ok) { nodes.sourceStatus.textContent = data.message; return; }
        sourceJob = data.job_id; check();
      } catch (_) {
        if (current === epoch && selection === sourceRequest) nodes.sourceStatus.textContent = "Příprava se nepotvrdila. Zkus znovu otevřít zdroj.";
      }
    }
    function mark(key) {
      const row = selectedRow(); if (!row || nodes[key === "in_ms" ? "start" : "end"].disabled) return;
      const source = model.sources.find(s => s.asset_id === selected);
      const ms = Math.max(0, Math.min(source.duration_ms, Math.round(nodes.sourcePlayer.currentTime * 1000)));
      if (!Number.isFinite(ms) || (key === "in_ms" ? ms > row.out_ms - 100 : ms < row.in_ms + 100)) {
        nodes.sourceStatus.textContent = "Konec musí být alespoň 0,1 sekundy za začátkem. Posuň video nebo uprav číselné časy."; return;
      }
      playingSelection = false; nodes.sourcePlayer.pause(); row[key] = ms; change(); renderRows();
    }
    function boundSelection() {
      cancel(selectionTimer);
      const row = selectedRow(); if (!playingSelection || !row) return;
      if (nodes.sourcePlayer.currentTime >= row.out_ms / 1000) {
        playingSelection = false; nodes.sourcePlayer.pause(); nodes.sourcePlayer.currentTime = row.out_ms / 1000;
      } else if (!nodes.sourcePlayer.paused) selectionTimer = later(boundSelection, 40);
    }
    function invalidate(message = "Projekt nelze nyní ověřit. Starší film se nezobrazuje.") {
      for (const audio of photoAudios) { audio.pause(); audio.removeAttribute("src"); audio.load(); }
      photoAudios = []; photoStatuses = []; photoOpen = null;
      ++epoch; model = null; dirty = false; pending = null; preserved = null;
      cancel(timer); stopPlayer(); stopSource();
      for (const key of ["shots", "voices", "jobs", "texts", "cards"]) nodes[key]?.replaceChildren();
      for (const key of ["save", "preview", "final", "range"]) nodes[key].disabled = true;
      nodes.status.textContent = message;
    }
    function conceal() {
      const keep = model && (dirty || pending) ? {model, pending, version} : preserved;
      invalidate(); preserved = keep;
    }
    function controls() {
      nodes.save.disabled = !model || saving || deleting || !dirty;
      for (const key of ["preview", "final", "range"]) nodes[key].disabled = !model || dirty || saving || deleting;
      for (const button of deleteButtons) button.disabled = deleting;
    }
    function change() {
      dirty = true; ++version; controls();
      if (playingSelection) nodes.sourcePlayer.pause();
      playingSelection = false; cancel(selectionTimer); syncSelection();
      nodes.status.textContent = "Úpravy čekají na uložení…";
      photoStatus("Úpravy čekají na uložení…");
      cancel(timer); timer = later(() => save(), 700);
    }
    function field(parent, label, row, key, {seconds = false, max = null} = {}) {
      const wrapper = text("label", label);
      const input = doc.createElement("input");
      input.type = key === "title" ? "text" : "number";
      if (input.type === "text") input.maxLength = 140;
      else { input.min = "0"; input.step = seconds ? "0.001" : "0.05"; if (max !== null) input.max = String(max); }
      input.value = seconds ? row[key] / 1000 : row[key];
      input.addEventListener("change", () => {
        row[key] = input.type === "text" ? input.value : seconds ? Math.round(Number(input.value) * 1000) : Number(input.value);
        change();
      });
      wrapper.appendChild(input); parent.appendChild(wrapper);
    }
    function renderRows() {
      const sources = new Map(model.sources.map(s => [s.asset_id, s]));
      for (const audio of photoAudios) audio.pause();
      photoAudios = []; photoStatuses = []; photoPanels = new Map();
      nodes.shots.replaceChildren(); nodes.voices.replaceChildren();
      for (const [index, row] of model.draft.shots.entries()) {
        const source = sources.get(row.asset_id), li = doc.createElement("li");
        const heading = text("strong", `${index + 1}. ${source.kind === "photo" ? "Fotografie" : "Video"} · ${source.title || "Bez názvu"}`);
        li.appendChild(heading);
        const checkbox = doc.createElement("input"), label = text("label", "Zařadit do filmu ");
        checkbox.type = "checkbox"; checkbox.checked = row.included;
        checkbox.addEventListener("change", () => { row.included = checkbox.checked; change(); });
        label.appendChild(checkbox); li.appendChild(label);
        const fields = doc.createElement("div"); fields.className = "camino-film-fields";
        field(fields, "Titulek", row, "title");
        if (source.kind === "photo") field(fields, "Délka (s)", row, "out_ms", {seconds: true, max: 300});
        else {
          field(fields, "Začátek ve videu (s)", row, "in_ms", {seconds: true, max: source.duration_ms / 1000});
          field(fields, "Konec ve videu (s)", row, "out_ms", {seconds: true, max: source.duration_ms / 1000});
          field(fields, "Zvuk videa (0–1)", row, "gain", {max: 1});
        }
        li.appendChild(fields);
        const actions = doc.createElement("div"); actions.className = "actions";
        if (source.kind === "video") {
          const open = text("button", "Otevřít video pro střih"); open.type = "button"; open.className = "secondary";
          open.addEventListener("click", () => selectVideo(row.asset_id)); actions.appendChild(open);
        } else {
          const open = text("a", "Otevřít fotografii");
          open.href = `/api/camino/film/photo/${model.project_id}/${row.asset_id}`;
          open.target = "_blank"; open.rel = "noopener noreferrer"; actions.appendChild(open);
        }
        for (const [label, delta] of [["↑ Dříve", -1], ["↓ Později", 1]]) {
          const b = text("button", label); b.type = "button"; b.className = "secondary";
          b.disabled = index + delta < 0 || index + delta >= model.draft.shots.length;
          b.addEventListener("click", () => {
            const list = model.draft.shots;
            [list[index], list[index + delta]] = [list[index + delta], list[index]];
            change(); renderRows();
          }); actions.appendChild(b);
        }
        {
          const preview = text("button", "Vytvořit náhled záběru s titulkem"); preview.type = "button"; preview.className = "secondary";
          preview.addEventListener("click", async () => {
            if (!await save()) return;
            const start = shotStart(row.asset_id);
            if (start !== null) { await render("preview", {start_ms: start, end_ms: start + row.out_ms - row.in_ms}); return; }
            nodes.status.textContent = "Záběr je vyřazený. Zařaď ho před vytvořením náhledu.";
          }); actions.appendChild(preview);
        }
        if (source.kind === "photo") {
          const edit = text("button", "Text a komentář"); edit.type = "button";
          edit.addEventListener("click", () => { photoOpen = row.asset_id; renderRows(); }); actions.appendChild(edit);
        }
        li.appendChild(actions);
        if (source.kind === "photo") photoPanel(li, row);
        nodes.shots.appendChild(li);
      }
      for (const row of model.draft.voices) {
        const source = sources.get(row.asset_id), li = doc.createElement("li");
        li.appendChild(text("strong", `${source.title || "Zvuková část"} · ${source.duration_ms / 1000} s${source.captured_local ? ` · ${source.captured_local.replace("T", " ")}` : ""}`));
        const checkbox = doc.createElement("input"), label = text("label", "Použít jako komentář ");
        checkbox.type = "checkbox"; checkbox.checked = row.included;
        checkbox.addEventListener("change", () => { row.included = checkbox.checked; change(); });
        label.appendChild(checkbox); li.appendChild(label);
        const fields = doc.createElement("div"); fields.className = "camino-film-fields";
        if (row.photo_asset_id) {
          fields.appendChild(text("p", "Komentář se přesouvá se svou fotografií."));
          const detach = text("button", "Odpojit od fotografie"); detach.type = "button";
          detach.addEventListener("click", () => { row.at_ms = shotStart(row.photo_asset_id) || 0; delete row.photo_asset_id; change(); renderRows(); });
          fields.appendChild(detach);
        } else field(fields, "Umístění ve filmu (s)", row, "at_ms", {seconds: true});
        field(fields, "Začátek nahrávky (s)", row, "in_ms", {seconds: true, max: source.duration_ms / 1000});
        field(fields, "Konec nahrávky (s)", row, "out_ms", {seconds: true, max: source.duration_ms / 1000});
        field(fields, "Hlasitost (0–1)", row, "gain", {max: 1});
        li.appendChild(fields);
        voiceActions(li, row, source);
        nodes.voices.appendChild(li);
      }
      if (!model.draft.voices.length) nodes.voices.appendChild(text("li", "Pro tento den není v uzavřené sadě žádný povolený hlasový komentář."));
      renderTexts();
      nodes.duck.value = model.draft.duck_gain;
      syncSelection();
    }
    function timeline() {
      const cards = model.draft.cards || [], rows = [];
      function after(id) {
        for (const card of cards) if (card.included && card.after_asset_id === id)
          rows.push({in_ms: 0, out_ms: card.duration_ms});
      }
      after(null);
      for (const row of model.draft.shots) { if (row.included) rows.push(row); after(row.asset_id); }
      return rows;
    }
    function shotStart(assetId) {
      let cursor = 0;
      for (const row of timeline()) {
        if (row.asset_id === assetId) return cursor;
        cursor += row.out_ms - row.in_ms;
      }
      return null;
    }
    function shotChoice(parent, momentId, {cards = false, value = null, photos = false} = {}) {
      const label = text("label", cards ? "Kartu umístit " : "Obrazový záběr ");
      const select = doc.createElement("select");
      if (cards) { const o = text("option", "Na začátek filmu"); o.value = ""; select.appendChild(o); }
      for (const [index, row] of model.draft.shots.entries()) {
        if (!cards && !row.included) continue;
        const source = model.sources.find(s => s.asset_id === row.asset_id);
        if (photos && source.kind !== "photo") continue;
        const option = text("option", `${cards ? "Za " : ""}${index + 1}. ${source.title || (source.kind === "photo" ? "Fotografie" : "Video")}${row.included ? "" : " (obraz vyřazen)"}`);
        option.value = row.asset_id; select.appendChild(option);
      }
      const related = model.draft.shots.find(r => r.included && (!photos || model.sources.find(s => s.asset_id === r.asset_id)?.kind === "photo") && model.sources.find(s => s.asset_id === r.asset_id)?.moment_id === momentId);
      if (value !== null) select.value = value;
      else if (related) select.value = related.asset_id;
      label.appendChild(select); parent.appendChild(label); return select;
    }
    function voiceActions(li, row, source) {
      const actions = doc.createElement("div"); actions.className = "actions";
      const listen = text("button", "Poslechnout / vybrat úsek"); listen.type = "button"; listen.className = "secondary";
      listen.addEventListener("click", () => selectVideo(row.asset_id)); actions.appendChild(listen);
      const target = shotChoice(actions, source.moment_id, {photos: true, value: row.photo_asset_id || null});
      const insert = text("button", "Vložit komentář k záběru"); insert.type = "button";
      insert.addEventListener("click", () => {
        const start = shotStart(target.value), duration = row.out_ms - row.in_ms;
        if (start === null) { feedback.textContent = "Nejprve vyber zařazenou fotografii."; return; }
        const photo = model.draft.shots.find(r => r.asset_id === target.value);
        if (duration > photo.out_ms) { feedback.textContent = `Komentář potřebuje ${(duration / 1000).toFixed(1)} s. Prodluž fotografii nebo vyber kratší úsek.`; return; }
        const end = start + duration, total = timeline().reduce((n, r) => n + r.out_ms - r.in_ms, 0);
        if (end > total) { nodes.status.textContent = `Komentář přesahuje obraz o ${((end - total) / 1000).toFixed(1)} s. Prodluž fotografie, přidej textovou kartu nebo ručně vyber kratší úsek řeči.`; return; }
        if (model.draft.voices.some(v => { const at = v.photo_asset_id ? shotStart(v.photo_asset_id) : v.at_ms; return v !== row && v.included && at !== null && start < at + v.out_ms - v.in_ms && end > at; })) {
          feedback.textContent = "Na tomto místě už je jiný komentář. Vyber jinou fotografii nebo uprav umístění."; return;
        }
        row.at_ms = start; row.photo_asset_id = photo.asset_id; row.included = true; change(); renderRows();
      });
      actions.appendChild(insert);
      const feedback = text("p", "Komentář lze navázat na fotografii; zůstane u ní i po přesunu.");
      photoStatuses.push(feedback);
      const extend = text("button", "Prodloužit fotografii pro komentář"); extend.type = "button";
      extend.addEventListener("click", () => {
        const photo = model.draft.shots.find(r => r.asset_id === target.value), duration = row.out_ms - row.in_ms;
        if (!photo || duration > 300000) { feedback.textContent = "Vyber fotografii a úsek nejvýše 300 sekund."; return; }
        photo.out_ms = Math.max(photo.out_ms, duration); change(); renderRows();
      }); actions.appendChild(extend); li.appendChild(actions); li.appendChild(feedback);
    }
    function focusPhoto(id) { photoPanels.get(id)?.scrollIntoView?.({block: "start", behavior: "smooth"}); }
    function photoStatus(message) { for (const node of photoStatuses) node.textContent = message; }
    function emptyLayer() { return {text: "", mode: "none", text_source: null, narration: null}; }
    function readingMs(value) { return Math.max(5000, Math.ceil(Math.max(value.trim().split(/\s+/).filter(Boolean).length / 2.5, value.length / 15)) * 1000); }
    function photoPanel(parent, row) {
      const panel = doc.createElement("details"); photoPanels.set(row.asset_id, panel); panel.open = photoOpen === row.asset_id;
      panel.addEventListener("toggle", () => { if (panel.open) photoOpen = row.asset_id; });
      panel.appendChild(text("summary", "Text a komentář fotografie"));
      const image = doc.createElement("img"); image.src = `/api/camino/film/photo/${model.project_id}/${row.asset_id}`;
      image.alt = "Fotografie pro text a komentář"; image.loading = "lazy"; image.className = "camino-film-photo"; panel.appendChild(image);
      const layer = () => row.photo_text ||= emptyLayer();
      const label = text("label", "Text fotografie — původní deník se nemění");
      const area = doc.createElement("textarea"); area.rows = 7; area.value = row.photo_text?.text || "";
      label.appendChild(area); panel.appendChild(label);
      const count = text("p", ""), feedback = text("p", "Úpravy se ukládají automaticky."); feedback.role = "status";
      photoStatuses.push(feedback);
      function lengthInfo() {
        const n = row.photo_text?.narration;
        count.textContent = `${area.value.length} / 6000 znaků · fotografie ${(row.out_ms / 1000).toFixed(1)} s · ` +
          `orientační čas pro celý text ${readingMs(area.value) / 1000} s` + (n ? ` · čtení ${(n.duration_ms / 1000).toFixed(1)} s` : "");
      }
      const modeLabel = text("label", "Způsob použití textu"), mode = doc.createElement("select");
      for (const [value, title] of [["none", "Pouze uložit text"], ["static", "Statický text přes fotografii"], ["scroll", "Plynulý text v okně"], ["narration", "Přečíst jako komentář — syntetický hlas"]]) {
        const option = text("option", title); option.value = value; mode.appendChild(option);
      }
      mode.value = row.photo_text?.mode || "none"; modeLabel.appendChild(mode); panel.appendChild(modeLabel);
      const audio = doc.createElement("audio"); audio.controls = true; audio.preload = "none"; photoAudios.push(audio);
      if (row.photo_text?.narration) audio.src = `/api/camino/film/narration/${model.project_id}/${row.photo_text.narration.id}`;
      area.addEventListener("input", () => {
        const current = layer(); current.text = area.value; current.narration = null;
        audio.pause(); audio.removeAttribute("src"); audio.load(); change(); lengthInfo();
      });
      mode.addEventListener("change", () => {
        layer().mode = mode.value; change();
        feedback.textContent = mode.value === "scroll" ? "Pro celý text zkontroluj doporučenou délku. Náhled i export používají stejné okno." :
          mode.value === "static" ? "Dlouhý statický text vyžaduje výběr úryvku. Celý dlouhý text zobrazí plynulý režim." :
          mode.value === "narration" ? "Vytvoř čtení, poslechni si ho a pak ho výslovně použij ve filmu." : "Text se ukládá bez zobrazení ve filmu.";
      });
      shotTextChoice(panel, row);
      const actions = doc.createElement("div"); actions.className = "actions";
      function button(title, fn) { const b = text("button", title); b.type = "button"; b.addEventListener("click", fn); actions.appendChild(b); return b; }
      button("Prodloužit pro celý text / čtení", () => {
        const current = layer(), ms = current.mode === "narration" && current.narration ? current.narration.duration_ms : readingMs(current.text);
        if (ms > 300000) { feedback.textContent = "Celý text potřebuje více než 300 sekund. Vyber kratší část textu."; return; }
        row.out_ms = Math.max(row.out_ms, ms); change(); renderRows();
      });
      const generate = button("Vytvořit místní čtení", async () => {
        if (narrating) { feedback.textContent = "Čtení se již vytváří. Počkej na výsledek."; return; }
        if (!layer().text.trim()) { feedback.textContent = "Nejprve napiš nebo vyber text."; return; }
        if (!await save()) return;
        const currentEpoch = epoch, snapshot = JSON.stringify(row.photo_text), project = model.project_id;
        narrating = true; generate.disabled = true; feedback.textContent = "Vytvářím místní české čtení na Macu…";
        try {
          const response = await request("/api/camino/film/narration", {method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({project_id: project, revision: model.revision, asset_id: row.asset_id, request_id: uuid()})});
          const data = await response.json();
          if (currentEpoch !== epoch || !active || doc.hidden) return;
          const live = model.draft.shots.find(r => r.asset_id === row.asset_id);
          if (JSON.stringify(live?.photo_text) !== snapshot) { feedback.textContent = "Text se mezitím změnil. Čtení se nepřipojilo."; return; }
          if (!data.ok) { feedback.textContent = data.message; return; }
          live.photo_text.narration = data.narration; change();
          if (await save()) { renderRows(); photoStatus("Čtení je uložené. Poslechni si ho a pak použij ve filmu."); }
        } catch (_) { if (currentEpoch === epoch) feedback.textContent = "Výsledek čtení není potvrzený. Automaticky jej neopakuji; text zůstává uložený."; }
        finally { narrating = false; generate.disabled = false; }
      });
      button("Použít čtení ve filmu", () => {
        const current = layer(), n = current.narration;
        if (!n) { feedback.textContent = "Nejprve vytvoř a poslechni čtení."; return; }
        if (n.duration_ms > row.out_ms) { feedback.textContent = `Čtení má ${(n.duration_ms / 1000).toFixed(1)} s. Nejprve prodluž fotografii nebo zkrať text.`; return; }
        current.mode = "narration"; n.included = true; change(); renderRows();
      });
      button("Vyřadit čtení z filmu", () => {
        const current = layer(); if (current.narration) current.narration.included = false;
        if (current.mode === "narration") current.mode = "none";
        change(); renderRows();
      });
      button("Náhled fotografie s textem a zvukem", async () => {
        if (!await save()) return;
        const start = shotStart(row.asset_id);
        if (start === null) { feedback.textContent = "Nejprve zařaď fotografii do filmu."; return; }
        await render("preview", {start_ms: start, end_ms: start + row.out_ms});
      });
      const recordings = doc.createElement("select"), recordingLabel = text("label", "Původní nahrávka k fotografii");
      for (const voice of model.draft.voices) {
        const option = text("option", model.sources.find(s => s.asset_id === voice.asset_id)?.title || "Komentář");
        option.value = voice.asset_id; recordings.appendChild(option);
      }
      recordingLabel.appendChild(recordings); panel.appendChild(recordingLabel);
      const recording = () => model.draft.voices.find(v => v.asset_id === recordings.value) || model.draft.voices[0];
      const attach = button("Připojit vybranou nahrávku k fotografii", () => {
        const voice = recording(); if (!voice) return;
        if (!row.included) { feedback.textContent = "Nejprve zařaď fotografii do filmu."; return; }
        if (voice.out_ms - voice.in_ms > row.out_ms) { feedback.textContent = "Nahrávka je delší než fotografie. Prodluž fotografii pro nahrávku nebo vyber kratší úsek řeči."; return; }
        voice.photo_asset_id = row.asset_id; voice.at_ms = shotStart(row.asset_id) || 0; voice.included = true; change(); renderRows();
      }); attach.disabled = !model.draft.voices.length;
      const extendRecording = button("Prodloužit fotografii pro nahrávku", () => {
        const voice = recording(); if (!voice) return;
        const duration = voice.out_ms - voice.in_ms;
        if (duration > 300000) { feedback.textContent = "Nahrávka přesahuje 300 sekund; nejprve ručně vyber kratší úsek."; return; }
        row.out_ms = Math.max(row.out_ms, duration); change(); renderRows();
      }); extendRecording.disabled = !model.draft.voices.length;
      const listenRecording = button("Poslechnout vybranou nahrávku", () => { const voice = recording(); if (voice) selectVideo(voice.asset_id); });
      listenRecording.disabled = !model.draft.voices.length;
      panel.appendChild(count); panel.appendChild(actions); panel.appendChild(audio); panel.appendChild(feedback);
      if (row.photo_text?.narration) panel.appendChild(text("p", row.photo_text.mode === "narration" && row.photo_text.narration.included ? "Syntetický komentář je zařazený do filmu." : "Čtení je uložené pro poslech, ve filmu zatím nezní."));
      lengthInfo(); parent.appendChild(panel);
    }
    function shotTextChoice(panel, row) {
      const select = doc.createElement("select"), label = text("label", "Nabídka přijatých textů deníku");
      for (const [index, source] of (model.texts || []).entries()) { const o = text("option", source.title || `Text ${index + 1}`); o.value = String(index); select.appendChild(o); }
      label.appendChild(select); panel.appendChild(label);
      const use = text("button", "Převzít celý vybraný text k fotografii"); use.type = "button"; use.disabled = !(model.texts || []).length;
      use.addEventListener("click", () => {
        const source = model.texts[Number(select.value || 0)]; if (!source) return;
        if (source.text.length > 6000) { photoStatus("Text má více než 6000 znaků. Vlož do fotografie vědomě vybraný úryvek."); return; }
        if (row.photo_text?.text && !(options.confirm || confirm)("Nahradit uložený text této fotografie vybraným textem deníku?")) return;
        row.photo_text = {text: source.text, mode: "none", text_source: {...source.reference}, narration: null};
        photoOpen = row.asset_id; change(); renderRows(); focusPhoto(row.asset_id);
      }); panel.appendChild(use); return select;
    }
    function renderTexts() {
      if (!nodes.texts || !nodes.cards) return;
      nodes.texts.replaceChildren(); nodes.cards.replaceChildren();
      nodes.texts.appendChild(text("li", "Text přes fotografii a čtení nastav přímo u fotografie tlačítkem Text a komentář. Zde jsou přijaté zdroje a samostatné karty mezi záběry."));
      for (const source of model.texts || []) {
        const li = doc.createElement("li"); li.appendChild(text("strong", source.title || "Text deníku"));
        li.appendChild(text("p", `${source.text.length} znaků. Celý text lze převzít a upravit přímo u fotografie.`));
        const actions = doc.createElement("div"); actions.className = "actions";
        const target = shotChoice(actions, source.reference.moment_id, {photos: true});
        const feedback = text("p", ""); feedback.role = "status";
        const transfer = text("button", "Předat celý text na fotografii"); transfer.type = "button";
        transfer.addEventListener("click", () => {
          const row = model.draft.shots.find(r => r.asset_id === target.value);
          if (!row) { feedback.textContent = "Vyber zařazenou fotografii."; return; }
          if (source.text.length > 6000) { feedback.textContent = "Text přesahuje 6000 znaků. Vlož u fotografie vlastní úryvek."; return; }
          if (row.photo_text?.text && !(options.confirm || confirm)("Nahradit text vybrané fotografie?")) return;
          row.photo_text = {text: source.text, mode: "none", text_source: {...source.reference}, narration: null};
          photoOpen = row.asset_id; change(); renderRows(); focusPhoto(row.asset_id);
          photoStatus("Celý text je u fotografie. Vyber statické zobrazení, plynulý text nebo čtení.");
        }); actions.appendChild(transfer);
        const card = text("button", "Přidat samostatnou textovou kartu za fotografii"); card.type = "button"; card.className = "secondary";
        card.addEventListener("click", () => {
          if (!target.value || source.text.length > 1000) { feedback.textContent = "Samostatná karta vyžaduje fotografii a nejvýše 1000 znaků. Delší text předej přímo na fotografii."; return; }
          if ((model.draft.cards || []).length >= 32) { feedback.textContent = "Film už má 32 samostatných karet."; return; }
          (model.draft.cards ||= []).push({id: uuid(), after_asset_id: target.value, text: source.text,
            duration_ms: 5000, included: true, text_source: {...source.reference}}); change(); renderRows();
        }); actions.appendChild(card); li.appendChild(actions); li.appendChild(feedback); nodes.texts.appendChild(li);
      }
      for (const card of model.draft.cards || []) {
        const li = doc.createElement("li"), label = text("label", "Zařadit samostatnou kartu "), checkbox = doc.createElement("input");
        checkbox.type = "checkbox"; checkbox.checked = card.included;
        checkbox.addEventListener("change", () => { card.included = checkbox.checked; change(); }); label.appendChild(checkbox); li.appendChild(label);
        const cardText = doc.createElement("textarea"); cardText.value = card.text; cardText.maxLength = 1000;
        cardText.addEventListener("input", () => { card.text = cardText.value; change(); }); li.appendChild(cardText); field(li, "Délka karty (s)", card, "duration_ms", {seconds: true, max: 300});
        const anchor = shotChoice(li, null, {cards: true, value: card.after_asset_id || ""});
        anchor.addEventListener("change", () => { card.after_asset_id = anchor.value || null; change(); }); nodes.cards.appendChild(li);
      }
    }
    function renderJobs(jobs) {
      nodes.jobs.replaceChildren();
      deleteButtons = [];
      const labels = {queued: "Ve frontě", rendering: "Vytváří se", ready: "Hotovo", failed: "Selhalo — lze zopakovat", interrupted: "Přerušeno — lze zopakovat", delete_pending: "Mazání nebylo dokončeno"};
      const key = j => JSON.stringify([j.revision, j.profile, j.range]);
      const exports = jobs.filter(j => !j.source_asset_id);
      const completed = new Set(exports.filter(j => j.state === "ready").map(key));
      for (const job of exports.slice().reverse()) {
        const superseded = ["failed", "interrupted"].includes(job.state) && completed.has(key(job));
        const li = text("li", `${job.profile === "final" ? "MP4 1080p" : "Náhled 720p"} · revize ${job.revision}${job.revision !== model.revision ? " (starší střih)" : ""}${job.range ? ` · dílčí úsek ${(job.range.start_ms / 1000).toFixed(1)}–${(job.range.end_ms / 1000).toFixed(1)} s` : ""} · ${superseded ? "Starší neúspěšný pokus; hotový výsledek je výše" : labels[job.state] || "Neznámý stav"}${job.state === "rendering" ? ` ${job.progress} %` : ""}`);
        if (job.message) li.appendChild(text("p", job.message));
        if (job.state === "ready" && safeOutput(job.url)) {
          const play = text("button", "Přehrát"); play.type = "button"; play.className = "secondary";
          play.addEventListener("click", () => { nodes.sourcePlayer.pause(); playingSelection = false; stopPlayer(); nodes.player.src = job.url; nodes.player.load(); });
          li.appendChild(play);
          const link = text("a", "Otevřít / uložit MP4"); link.href = job.url; link.target = "_blank"; link.rel = "noopener";
          li.appendChild(link);
        }
        if (!superseded && ["failed", "interrupted", "queued"].includes(job.state)) {
          const retry = text("button", "Zopakovat / pokračovat"); retry.type = "button"; retry.className = "secondary";
          retry.addEventListener("click", () => render(job.profile, job.range, job.revision, job.state === "queued" || job.state === "interrupted" ? job.job_id : null));
          li.appendChild(retry);
        }
        if (["ready", "failed", "interrupted", "delete_pending"].includes(job.state)) {
          const remove = text("button", job.state === "delete_pending" ? "Dokončit smazání" : "Smazat natrvalo");
          remove.type = "button"; remove.className = "secondary"; remove.disabled = deleting;
          remove.addEventListener("click", () => removeExport(job)); deleteButtons.push(remove); li.appendChild(remove);
        }
        nodes.jobs.appendChild(li);
      }
    }
    async function removeExport(job) {
      if (!model || deleting) return;
      if (dirty || saving || preserved) { save(); nodes.status.textContent = "Nejprve dokonči uložení střihu; potom můžeš smazat variantu."; return; }
      const current = epoch, selection = {project_id: model.project_id, job_id: job.job_id};
      deleting = true; ++readRequest; controls(); let refresh = false, message = "";
      try {
        const response = await request("/api/camino/film/delete-plan", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(selection)});
        const plan = await response.json();
        if (current !== epoch || !active || doc.hidden) return;
        if (!plan.ok) { message = plan.message || "Rozsah smazání nelze ověřit."; return; }
        if (plan.project_id !== selection.project_id || plan.job_id !== selection.job_id ||
            !/^[a-f0-9]{64}$/.test(plan.plan_token) || plan.revision !== job.revision || plan.profile !== job.profile ||
            !(plan.range === null && job.range === null || plan.range && job.range &&
              plan.range.start_ms === job.range.start_ms && plan.range.end_ms === job.range.end_ms)) { message = "Potvrzení patří jiné variantě. Znovu načti přehled."; return; }
        if (plan.already_deleted) { refresh = true; message = "Varianta už byla trvale smazaná."; return; }
        const label = `${plan.profile === "final" ? "MP4 1080p" : "Náhled 720p"} · revize ${plan.revision}` +
          (plan.range ? ` · úsek ${(plan.range.start_ms / 1000).toFixed(1)}–${(plan.range.end_ms / 1000).toFixed(1)} s` : " · celý film");
        const answer = askDelete(`${label}\n\nTrvale odstranit tuto variantu včetně pracovních souborů: ${(plan.bytes / 1000000).toLocaleString("cs-CZ", {maximumFractionDigits: 1})} MB, ${plan.file_count} souborů.\nBez koše a nové kopie. Zdrojové záznamy a uložený střih zůstanou.\n\nPro smazání napiš přesně:\n${plan.confirmation_text}`);
        if (answer === null) return;
        if (answer !== plan.confirmation_text) { message = "Potvrzovací věta nesouhlasí. Varianta zůstala zachovaná."; return; }
        if (nodes.player.getAttribute("src") === job.url) stopPlayer();
        refresh = true; nodes.status.textContent = "Trvale odstraňuji vybranou variantu…";
        const removed = await request("/api/camino/film/delete", {method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({...selection, plan_token: plan.plan_token, confirmation: answer})});
        const result = await removed.json();
        message = result.ok ? "Varianta a její pracovní soubory byly trvale smazané." : (result.message || "Smazání se nedokončilo. Obnov přehled a zkontroluj stav.");
      } catch (_) { message = "Výsledek smazání není potvrzený. Obnov přehled; smazání se automaticky neopakuje."; }
      finally {
        deleting = false;
        if (current === epoch && active) {
          if (refresh) await check();
          controls(); if (message) nodes.status.textContent = message;
        }
      }
    }
    async function check() {
      if (!active || doc.hidden || deleting) return;
      const current = epoch, read = ++readRequest;
      try {
        const response = await request("/api/camino/film/editor" + (requestedProject ? `?project_id=${encodeURIComponent(requestedProject)}` : ""), {cache: "no-store"});
        const data = await response.json();
        if (current !== epoch || read !== readRequest || !active || doc.hidden) return;
        if (!data.ok) { invalidate(data.message); return; }
        if (requestedProject && data.project_id !== requestedProject) { invalidate("Odpověď patří jinému filmu. Znovu otevři projekt."); return; }
        if (preserved) {
          if (preserved.model.project_id === data.project_id) {
            model = preserved.model; pending = preserved.pending; version = preserved.version; dirty = true;
            renderRows(); nodes.status.textContent = "Neuložené úpravy jsou obnovené. Ulož je nebo načti poslední revizi.";
          }
          preserved = null;
        }
        if (!model || (!dirty && !saving && model.revision !== data.revision)) {
          model = data; renderRows();
          nodes.status.textContent = `Uložená revize ${data.revision} · ${(data.duration_ms / 1000).toLocaleString("cs-CZ")} s. Úpravy se ukládají automaticky.`;
        }
        if (model.project_id !== data.project_id) { invalidate("Uzavřená sada se změnila. Znovu načti editor."); return; }
        if (dirty && model.revision !== data.revision && !saving) nodes.status.textContent = "Jiné okno uložilo novější střih. Tvoje změny zůstávají zde; před pokračováním načti poslední revizi.";
        renderJobs(data.jobs); updateSource(data.jobs); controls();
      } catch (_) { if (current === epoch && read === readRequest) conceal(); }
    }
    async function save() {
      cancel(timer);
      if (!model) return false;
      if (saving) { nodes.status.textContent = "Ukládání právě probíhá. Počkej na potvrzení."; return false; }
      if (!dirty && !pending) return true;
      const current = epoch;
      if (!pending) pending = {version, payload: {project_id: model.project_id, expected_revision: model.revision,
        request_id: uuid(), draft: JSON.parse(JSON.stringify(model.draft))}};
      const captured = pending;
      saving = true; controls();
      try {
        const response = await request("/api/camino/film/save", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(captured.payload)});
        const data = await response.json();
        if (current !== epoch) return false;
        if (!data.ok) { pending = null; nodes.status.textContent = data.message; photoStatus(data.message); return false; }
        model.revision = data.revision; pending = null; dirty = version !== captured.version;
        nodes.status.textContent = `Uložena revize ${data.revision}.${dirty ? " Zbývající úpravy se ukládají…" : ""}`;
        photoStatus(nodes.status.textContent);
        if (dirty) timer = later(() => save(), 100);
        return !dirty;
      } catch (_) {
        if (current === epoch) { nodes.status.textContent = "Odpověď se ztratila. Zkus Uložit střih znovu; stejné uložení se neduplikuje."; photoStatus(nodes.status.textContent); }
        return false;
      } finally { saving = false; controls(); }
    }
    async function render(profile, interval = null, revision = null, requestId = null) {
      if (!model || dirty || saving) { nodes.status.textContent = "Nejprve počkej na uložení střihu."; return; }
      const current = epoch;
      try {
        const response = await request("/api/camino/film/render", {method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({project_id: model.project_id, revision: revision || model.revision,
            request_id: requestId || uuid(), profile, range: interval})});
        const data = await response.json();
        if (current !== epoch) return;
        nodes.status.textContent = data.ok ? "Export je ve frontě. Stav se průběžně aktualizuje." : data.message;
        photoStatus(nodes.status.textContent);
        if (data.ok) check();
      } catch (_) { if (current === epoch) nodes.status.textContent = "Požadavek se nepotvrdil. Znovu načti stav fronty před opakováním."; }
    }
    nodes.save.addEventListener("click", () => save());
    nodes.start.addEventListener("click", () => mark("in_ms"));
    nodes.end.addEventListener("click", () => mark("out_ms"));
    nodes.playSelection.addEventListener("click", () => {
      const row = selectedRow(); if (!row || nodes.playSelection.disabled) return;
      nodes.player.pause(); nodes.sourcePlayer.currentTime = row.in_ms / 1000; playingSelection = true;
      const current = sourceRequest;
      nodes.sourcePlayer.play().catch(() => {
        if (current === sourceRequest) { playingSelection = false; nodes.sourceStatus.textContent = "Přehrávání se nespustilo. Zkus Přehrát výběr znovu."; }
      });
    });
    nodes.sourcePlayer.addEventListener("loadedmetadata", syncSelection);
    nodes.sourcePlayer.addEventListener("playing", boundSelection);
    nodes.sourcePlayer.addEventListener("timeupdate", boundSelection);
    nodes.sourcePlayer.addEventListener("pause", () => cancel(selectionTimer));
    nodes.sourcePlayer.addEventListener("seeking", () => {
      const row = selectedRow(), ms = nodes.sourcePlayer.currentTime * 1000;
      if (playingSelection && row && (ms < row.in_ms || ms >= row.out_ms)) { playingSelection = false; nodes.sourcePlayer.pause(); }
    });
    nodes.sourcePlayer.addEventListener("error", () => {
      if (selected) {
        playingSelection = false; sourceJob = null; cancel(sourceTimer); cancel(selectionTimer);
        nodes.sourcePlayer.pause(); nodes.sourcePlayer.removeAttribute("src"); nodes.sourcePlayer.load(); syncSelection();
        nodes.sourceStatus.textContent = "Zdroj nelze načíst. Znovu otevři video nebo komentář a ověř připojení.";
      }
    });
    nodes.preview.addEventListener("click", () => render("preview"));
    nodes.final.addEventListener("click", () => render("final"));
    nodes.range.addEventListener("click", () => render("preview", {start_ms: Math.round(Number(nodes.from.value) * 1000), end_ms: Math.round(Number(nodes.to.value) * 1000)}));
    nodes.duck.addEventListener("change", () => { if (model) { model.draft.duck_gain = Number(nodes.duck.value); change(); } });
    nodes.reload.addEventListener("click", () => {
      if (dirty && !(options.confirm || confirm)("Zahodit zdejší neuložené změny a načíst poslední uložený střih?")) return;
      invalidate("Načítám poslední uloženou revizi…"); check();
    });
    doc.addEventListener("visibilitychange", () => {
      if (!active) return;
      if (doc.hidden) { if (dirty) save(); conceal(); }
      else check();
    });
    return {
      open(projectId = null) {
        if (requestedProject !== projectId) {
          if (!this.canClose()) return false;
          invalidate(); requestedProject = projectId;
        }
        active = true; root.classList.remove("hidden"); check(); cancel(refreshTimer);
        const tick = () => { if (active) { check(); refreshTimer = later(tick, 10000); } }; refreshTimer = later(tick, 10000);
        return true;
      },
      close() { active = false; cancel(refreshTimer); invalidate(); root.classList.add("hidden"); },
      suspend() { active = false; cancel(refreshTimer); conceal(); root.classList.add("hidden"); },
      canClose() {
        if (narrating) { nodes.status.textContent = "Nejprve počkej na dokončení čtení fotografie."; return false; }
        if (deleting) { nodes.status.textContent = "Dokončuji smazání varianty. Před přepnutím počkej na výsledek."; return false; }
        if (preserved) { nodes.status.textContent = "Nejprve obnov spojení a ulož rozpracovaný střih."; return false; }
        if (dirty || saving) { save(); nodes.status.textContent = "Nejprve dokonči uložení změn; potom můžeš přepnout nebo zavřít film."; return false; }
        return true;
      },
      check, invalidate, save,
    };
  }
  window.SamanthaFilmEditor = {create};
})();
