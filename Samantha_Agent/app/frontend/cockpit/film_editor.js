(() => {
  "use strict";
  function create(root, options = {}) {
    const doc = options.document || document;
    const request = options.fetch || ((...args) => fetch(...args));
    const uuid = options.uuid || (() => crypto.randomUUID());
    const later = options.setTimeout || setTimeout;
    const cancel = options.clearTimeout || clearTimeout;
    const nodes = Object.fromEntries(["status", "shots", "voices", "jobs", "save", "preview", "final",
      "range", "from", "to", "duck", "player", "reload", "source", "sourcePlayer", "sourceStatus",
      "sourceTitle", "selection", "start", "end", "playSelection"].map(key => [key, root.querySelector(`[data-film="${key}"]`)]));
    let model = null, active = false, dirty = false, saving = false, version = 0, epoch = 0;
    let pending = null, timer = null, refreshTimer = null, preserved = null, readRequest = 0;
    let selected = null, sourceJob = null, sourceRequest = 0, sourceTimer = null, selectionTimer = null, playingSelection = false;
    function text(tag, value) { const n = doc.createElement(tag); n.textContent = value; return n; }
    function stopPlayer() { nodes.player.pause(); nodes.player.removeAttribute("src"); nodes.player.load(); }
    function stopSource() {
      ++sourceRequest; cancel(sourceTimer); cancel(selectionTimer); selected = null; sourceJob = null; playingSelection = false;
      nodes.sourcePlayer.pause(); nodes.sourcePlayer.removeAttribute("src"); nodes.sourcePlayer.load();
      nodes.source.classList.add("hidden");
      for (const key of ["start", "end", "playSelection"]) nodes[key].disabled = true;
    }
    function selectedRow() { return model?.draft.shots.find(row => row.asset_id === selected); }
    function safeOutput(url) {
      return typeof url === "string" && url.startsWith(`/api/camino/film/output/${model.project_id}/`)
        && url.split("/").length === 7 && /^[a-f0-9-]{36}$/.test(url.split("/")[6]);
    }
    function syncSelection() {
      const row = selectedRow(); if (!row) return;
      const source = model.sources.find(s => s.asset_id === selected);
      nodes.sourceTitle.textContent = `Video ${model.draft.shots.indexOf(row) + 1} · ${source.title || "Bez názvu"}`;
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
        nodes.sourceStatus.textContent = "Posuň video na požadované místo a označ začátek nebo konec. Přehrát výběr přehraje jen označenou část.";
      } else if (["failed", "interrupted"].includes(job.state)) {
        nodes.sourceStatus.textContent = "Náhled se nedokončil. Tlačítkem u záběru ho můžeš připravit znovu.";
      } else {
        nodes.sourceStatus.textContent = `Připravuji náhled videa${job.state === "rendering" ? ` · ${job.progress} %` : " · ve frontě"}…`;
        sourceTimer = later(() => check(), 1500);
      }
      syncSelection();
    }
    async function selectVideo(assetId) {
      if (!model) return;
      stopSource(); stopPlayer(); selected = assetId;
      const current = epoch, selection = sourceRequest;
      nodes.source.classList.remove("hidden"); syncSelection();
      nodes.sourceStatus.textContent = "Ověřuji a připravuji náhled celého videa…";
      nodes.source.scrollIntoView?.({block: "nearest", behavior: "smooth"});
      try {
        const response = await request("/api/camino/film/source", {method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({project_id: model.project_id, asset_id: assetId, request_id: uuid()})});
        const data = await response.json();
        if (current !== epoch || selection !== sourceRequest || !active || doc.hidden) return;
        if (!data.ok) { nodes.sourceStatus.textContent = data.message; return; }
        sourceJob = data.job_id; check();
      } catch (_) {
        if (current === epoch && selection === sourceRequest) nodes.sourceStatus.textContent = "Příprava se nepotvrdila. Zkus znovu otevřít video u záběru.";
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
      ++epoch; model = null; dirty = false; pending = null; preserved = null;
      cancel(timer); stopPlayer(); stopSource();
      for (const key of ["shots", "voices", "jobs"]) nodes[key].replaceChildren();
      for (const key of ["save", "preview", "final", "range"]) nodes[key].disabled = true;
      nodes.status.textContent = message;
    }
    function conceal() {
      const keep = model && (dirty || pending) ? {model, pending, version} : preserved;
      invalidate(); preserved = keep;
    }
    function controls() {
      nodes.save.disabled = !model || saving || !dirty;
      for (const key of ["preview", "final", "range"]) nodes[key].disabled = !model || dirty || saving;
    }
    function change() {
      dirty = true; ++version; controls();
      if (playingSelection) nodes.sourcePlayer.pause();
      playingSelection = false; cancel(selectionTimer); syncSelection();
      nodes.status.textContent = "Úpravy čekají na uložení…";
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
        const preview = text("button", "Vytvořit náhled záběru s titulkem"); preview.type = "button"; preview.className = "secondary";
        preview.addEventListener("click", async () => {
          if (!await save()) return;
          let start = 0;
          for (const item of model.draft.shots) {
            if (!item.included) continue;
            if (item === row) { await render("preview", {start_ms: start, end_ms: start + row.out_ms - row.in_ms}); return; }
            start += item.out_ms - item.in_ms;
          }
          nodes.status.textContent = "Záběr je vyřazený. Zařaď ho před vytvořením náhledu.";
        }); actions.appendChild(preview); li.appendChild(actions); nodes.shots.appendChild(li);
      }
      for (const row of model.draft.voices) {
        const source = sources.get(row.asset_id), li = doc.createElement("li");
        li.appendChild(text("strong", `${source.title || "Zvuková část"} · ${source.duration_ms / 1000} s`));
        const checkbox = doc.createElement("input"), label = text("label", "Použít jako komentář ");
        checkbox.type = "checkbox"; checkbox.checked = row.included;
        checkbox.addEventListener("change", () => { row.included = checkbox.checked; change(); });
        label.appendChild(checkbox); li.appendChild(label);
        const fields = doc.createElement("div"); fields.className = "camino-film-fields";
        field(fields, "Umístění ve filmu (s)", row, "at_ms", {seconds: true});
        field(fields, "Začátek nahrávky (s)", row, "in_ms", {seconds: true, max: source.duration_ms / 1000});
        field(fields, "Konec nahrávky (s)", row, "out_ms", {seconds: true, max: source.duration_ms / 1000});
        field(fields, "Hlasitost (0–1)", row, "gain", {max: 1});
        li.appendChild(fields); nodes.voices.appendChild(li);
      }
      nodes.duck.value = model.draft.duck_gain;
      syncSelection();
    }
    function renderJobs(jobs) {
      nodes.jobs.replaceChildren();
      const labels = {queued: "Ve frontě", rendering: "Vytváří se", ready: "Hotovo", failed: "Selhalo — lze zopakovat", interrupted: "Přerušeno — lze zopakovat"};
      const key = j => JSON.stringify([j.revision, j.profile, j.range]);
      const exports = jobs.filter(j => !j.source_asset_id);
      const completed = new Set(exports.filter(j => j.state === "ready").map(key));
      for (const job of exports.slice().reverse()) {
        const superseded = ["failed", "interrupted"].includes(job.state) && completed.has(key(job));
        const li = text("li", `${job.profile === "final" ? "MP4 1080p" : "Náhled 720p"} · revize ${job.revision}${job.revision !== model.revision ? " (starší střih)" : ""}${job.range ? " · dílčí úsek" : ""} · ${superseded ? "Starší neúspěšný pokus; hotový výsledek je výše" : labels[job.state] || "Neznámý stav"}${job.state === "rendering" ? ` ${job.progress} %` : ""}`);
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
        nodes.jobs.appendChild(li);
      }
    }
    async function check() {
      if (!active || doc.hidden) return;
      const current = epoch, read = ++readRequest;
      try {
        const response = await request("/api/camino/film/editor", {cache: "no-store"});
        const data = await response.json();
        if (current !== epoch || read !== readRequest || !active || doc.hidden) return;
        if (!data.ok) { invalidate(data.message); return; }
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
        if (!data.ok) { pending = null; nodes.status.textContent = data.message; return false; }
        model.revision = data.revision; pending = null; dirty = version !== captured.version;
        nodes.status.textContent = `Uložena revize ${data.revision}.${dirty ? " Zbývající úpravy se ukládají…" : ""}`;
        if (dirty) timer = later(() => save(), 100);
        return !dirty;
      } catch (_) {
        if (current === epoch) nodes.status.textContent = "Odpověď se ztratila. Zkus Uložit střih znovu; stejné uložení se neduplikuje.";
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
        nodes.sourceStatus.textContent = "Video nelze načíst. Znovu otevři video u záběru a ověř připojení.";
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
      open() { active = true; root.classList.remove("hidden"); check(); cancel(refreshTimer);
        const tick = () => { if (active) { check(); refreshTimer = later(tick, 10000); } }; refreshTimer = later(tick, 10000); },
      close() { active = false; cancel(refreshTimer); invalidate(); root.classList.add("hidden"); },
      canClose() { if (dirty || saving) { save(); nodes.status.textContent = "Nejprve dokonči uložení změn; potom můžeš okno zavřít."; return false; } return true; },
      check, invalidate, save,
    };
  }
  window.SamanthaFilmEditor = {create};
})();
