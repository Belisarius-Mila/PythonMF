(function (root) {
  "use strict";
  const emptyDraft = () => ({title: "", prompt: "", fixed_elements: "", source_ids: [], image_source_id: "", annotations: []});
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const scopeKey = scope => [scope.project, scope.room, scope.base || "base"].join(":");
  function gate() {
    let epoch = 0;
    return {begin: () => ++epoch, current: token => token === epoch};
  }
  function paths(strokes) {
    if (!Array.isArray(strokes)) return "";
    return strokes.slice(0, 100).map(stroke => {
      if (!Array.isArray(stroke) || stroke.length < 2 || stroke.length > 1000) return "";
      if (stroke.some(p => !Array.isArray(p) || p.length !== 2 || p.some(n => typeof n !== "number" || !Number.isFinite(n) || n < 0 || n > 1))) return "";
      return '<path d="' + stroke.map((p,i) => (i ? "L" : "M") + p.map(n => Math.round(n * 1000)).join(" ")).join(" ") + '"/>';
    }).join("");
  }
  function restoreDraft(server, cached) {
    const valid = value => value && ["title","prompt","fixed_elements","image_source_id"].every(k => typeof value[k] === "string") &&
      Array.isArray(value.source_ids) && value.source_ids.every(id => typeof id === "string") && Array.isArray(value.annotations);
    if (!cached || cached.dirty !== true || !valid(cached.draft) || !Number.isInteger(cached.revision)) {
      return {draft: Object.fromEntries(Object.keys(emptyDraft()).map(k => [k, server[k]])), revision: server.revision, dirty: false, conflict: false};
    }
    return {draft: cached.draft, revision: cached.revision, dirty: true, conflict: cached.revision !== server.revision};
  }
  const core = {emptyDraft, escape, scopeKey, gate, paths, restoreDraft};
  if (typeof module !== "undefined" && module.exports) module.exports = core;
  if (!root.document) return;
  const $ = id => document.getElementById(id);
  const loader = gate();
  let scope = {project: "", room: "", base: "base"}, data = {projects: [], room: null}, draft = emptyDraft();
  let revision = 0, dirty = false, busy = false, loading = false, view = "gallery", returnView = "gallery", notesOpen = true, drawing = false, comparing = false;
  let serverDraft = null;
  let selectedFiles = [], createMode = "project", cacheWarning = false;
  const aiLoader = gate();
  let aiState = {enabled:false, jobs:[]}, aiSending = false;
  const kindName = {photo: "Skutečný stav", plan: "Náčrt nebo rozměry", inspiration: "Inspirace"};

  function status(message, error = false) {
    $("status").textContent = message;
    $("status").dataset.error = String(error);
  }
  function cacheKey() { return "samantha-interior-draft-v1:" + scopeKey(scope); }
  function cacheRead(key) { try { return JSON.parse(localStorage.getItem(key) || "null"); } catch (_) { return null; } }
  function stash() {
    if (!scope.room) return;
    try { localStorage.setItem(cacheKey(), JSON.stringify({draft, revision, dirty, note: $("noteText").value, aiText: $("aiText").value})); }
    catch (_) { cacheWarning = true; status("Prohlížeč neuchová rozpracované změny. Použij Uložit rozpracováno.", true); }
  }
  function remember() {
    try { localStorage.setItem("samantha-interior-selection-v1", JSON.stringify(scope)); } catch (_) { /* Server saves remain available. */ }
  }
  function changed() { dirty = true; stash(); $("serverComparison").hidden = false; $("draftStatus").textContent = "Neuložené změny" + (cacheWarning ? " · ulož je před zavřením" : " · rozepsané zadání uchovává i tento prohlížeč"); }
  function sourceUrl(id, size = "preview") {
    return "/api/interior/asset?" + new URLSearchParams({project_id: scope.project, room_id: scope.room, asset_id: id, view: size});
  }
  async function api(path, payload) {
    const response = await fetch(path, payload ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)} : {cache: "no-store"});
    const value = await response.json();
    if (!response.ok || !value.ok) {
      const error = new Error(value.message || "Ateliér požadavek nedokončil.");
      error.code = value.error;
      throw error;
    }
    return value;
  }
  function context() { return {...scope}; }
  function setBusy(value) {
    busy = value;
    const locked = value || loading;
    ["projectSelect","roomSelect","newProject","newRoom","firstProject","refresh","uploadSources","confirmCreate","saveDraft","saveVariant","saveSourceSelection","noteText"].forEach(id => $(id).disabled = locked);
    $("noteForm").querySelector("button").disabled = locked;
    $("draftForm").querySelectorAll("input,textarea").forEach(el => el.disabled = locked);
    $("sourceFiles").disabled = locked;
    $("sourceKind").disabled = locked;
    $("newRoom").disabled = locked || !scope.project;
    $("sourceList").querySelectorAll("input").forEach(el => el.disabled = locked);
    if (data.room) renderAI();
  }
  async function mutate(action, details, captured = context()) {
    return api("/api/interior/action", {action, request_id: crypto.randomUUID(), ...details,
      ...(["create_project"].includes(action) ? {} : action === "create_room" ? {project_id: captured.project} : {
        project_id: captured.project, room_id: captured.room})});
  }
  async function perform(fn) {
    if (busy || loading) return;
    setBusy(true);
    try { await fn(); }
    catch (error) {
      if (error.code === "conflict" && scope.room) await load();
      status(error.message || "Výsledek není ověřený. Obnov stav a ověř, zda byl požadavek uložen.", true);
    }
    finally { setBusy(false); }
  }
  async function load(next = scope) {
    stash();
    const token = loader.begin();
    loading = true; setBusy(busy);
    const wanted = {...next};
    if (scopeKey(wanted) !== scopeKey(scope)) { aiLoader.begin(); aiState = {enabled:false,jobs:[],message:"Ověřuji architekta pro tuto místnost…"}; }
    let response;
    try {
      response = await api("/api/interior/state" + (wanted.room ? "?" + new URLSearchParams({
        project_id: wanted.project, room_id: wanted.room, base_id: wanted.base || "base"}) : ""));
    } catch (error) { if (loader.current(token)) { loading = false; setBusy(busy); status(error.message, true); } return; }
    if (!loader.current(token)) return;
    data = response;
    if (!wanted.room && data.projects.length) {
      const project = data.projects.find(p => p.id === wanted.project) || data.projects[0];
      return load({project: project.id, room: project.rooms[0].id, base: "base"});
    }
    scope = wanted;
    if (response.draft) {
      serverDraft = response.draft;
      const cached = cacheRead(cacheKey());
      const restored = restoreDraft(response.draft, cached);
      draft = restored.draft; revision = restored.revision; dirty = restored.dirty;
      $("noteText").value = cached && typeof cached.note === "string" ? cached.note : "";
      $("aiText").value = cached && typeof cached.aiText === "string" ? cached.aiText : "";
      status(restored.conflict ? "Server obsahuje novější zadání. Tvoje rozepsané změny zůstaly v editoru; před uložením je porovnej." :
        dirty ? "Obnovené neuložené změny." : "Načtený uložený stav.", restored.conflict);
    } else { draft = emptyDraft(); revision = 0; dirty = false; status("Vytvoř první projekt."); }
    remember(); render(); loading = false; setBusy(busy); refreshAI();
  }
  function picture(record, thumbnail = false) {
    if (!record || !record.image_source_id || !data.room.sources[record.image_source_id]) return '<div class="placeholder">Vyber pracovní obrázek v Podkladech.</div>';
    const source = data.room.sources[record.image_source_id];
    return '<div class="picture"><img alt="' + escape(source.title) + '" src="' + escape(sourceUrl(source.id, thumbnail ? "thumbnail" : "preview")) + '"><svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true">' + paths(record.annotations) + '</svg></div>';
  }
  function renderPicture() {
    const variant = data.room.variants[scope.base];
    if (comparing && variant && variant.parent_id) {
      const parent = data.room.variants[variant.parent_id];
      $("visual").innerHTML = '<div class="compare-grid"><figure>' + picture(parent) + '<figcaption>' + escape(parent.title) +
        '</figcaption></figure><figure>' + picture(variant) + '<figcaption>' + escape(variant.title) + '</figcaption></figure></div>';
    } else $("visual").innerHTML = picture(view === "edit" || scope.base === "base" ? draft : variant);
    $("draw").setAttribute("aria-pressed", String(drawing));
    const area = $("visual").querySelector(".picture");
    if (area && drawing && view === "edit") {
      area.classList.add("draw-mode");
      bindDrawing(area);
    }
  }
  function render() {
    const p = data.projects.find(p => p.id === scope.project);
    $("projectSelect").innerHTML = data.projects.map(p => '<option value="' + p.id + '">' + escape(p.title) + '</option>').join("");
    $("projectSelect").value = scope.project;
    $("roomSelect").innerHTML = (p ? p.rooms : []).map(r => '<option value="' + r.id + '">' + escape(r.title) + '</option>').join("");
    $("roomSelect").value = scope.room;
    $("newRoom").disabled = !p || busy;
    $("emptyProject").hidden = !!data.room;
    $("openSources").disabled = !data.room;
    $("workbench").hidden = !data.room || view === "sources";
    $("sourcesView").hidden = !data.room || view !== "sources";
    $("backToGallery").hidden = view === "gallery";
    $("toggleNotes").setAttribute("aria-pressed", String(notesOpen));
    $("notesPanel").hidden = !notesOpen;
    $("workbench").classList.toggle("no-notes", !notesOpen);
    $("workbench").classList.toggle("editing", view === "edit");
    if (!data.room) return;
    const current = data.room.variants[scope.base];
    const name = current ? current.title : draft.title || "Nové zadání";
    $("contextLabel").textContent = p.title + " / " + data.room.title;
    $("variantTitle").textContent = (view === "edit" ? "Úprava: " : "") + name;
    $("variantOrigin").textContent = current && current.parent_id ? "Vychází z: " + data.room.variants[current.parent_id].title : "Samostatné zadání";
    $("variants").innerHTML = Object.values(data.room.variants).map(v => '<button type="button" class="thumb ' + (v.id === scope.base ? "selected" : "") + '" data-variant="' + v.id + '">' +
      picture(v, true) + '<span class="thumb-label">' + escape(v.title) + '<span class="muted">' + (v.kind === "ai_proposal" ? "AI vizualizace" : "Uložené zadání s poznámkami") + '</span></span></button>').join("") ||
      '<p class="muted">Zatím bez uložených variant. Přidej podklady a připrav první zadání.</p>';
    $("variants").querySelectorAll("[data-variant]").forEach(button => button.addEventListener("click", () => {
      if (busy) return; view = "gallery"; comparing = false; drawing = false; load({...scope, base: button.dataset.variant});
    }));
    $("editor").hidden = view !== "edit";
    $("editVariant").hidden = view === "edit";
    $("compare").hidden = view === "edit";
    $("compare").disabled = !current || !current.parent_id;
    $("compare").setAttribute("aria-pressed", String(comparing));
    $("visualCaption").textContent = current && current.kind === "ai_proposal" && view !== "edit" ?
      "AI koncepční vizualizace · rozměry a proveditelnost je třeba ověřit" :
      "Pracovní podklad a kreslené poznámky · nejde o rozměrový výkres";
    $("draftTitle").value = draft.title || "";
    $("draftPrompt").value = draft.prompt || "";
    $("draftFixed").value = draft.fixed_elements || "";
    $("draftStatus").textContent = dirty ? "Neuložené změny" : "Rozpracováno uložené · verze " + revision;
    $("serverComparison").hidden = !dirty;
    $("serverDraftPreview").textContent = serverDraft ? "Název: " + serverDraft.title + "\n\nCo změnit:\n" + serverDraft.prompt +
      "\n\nCo zachovat:\n" + serverDraft.fixed_elements + "\n\nVybrané podklady: " + serverDraft.source_ids.length : "";
    $("notesContext").textContent = "K návrhu: " + name;
    $("notes").innerHTML = data.room.notes.filter(n => n.base_id === scope.base).map(n => '<div class="note">' + escape(n.text) + '</div>').join("");
    renderPicture(); renderSources(); renderAI();
  }
  function pendingAIKey(captured = scope) { return "samantha-interior-ai-send-v1:" + scopeKey(captured); }
  function pendingAI() { return cacheRead(pendingAIKey()); }
  function aiBlocked() { return (aiState.jobs || []).some(job => ["queued","running","delivery_unknown","result_ready"].includes(job.status)); }
  function renderAI() {
    if (!data.room) return;
    const count = new Set([draft.image_source_id, ...draft.source_ids].filter(Boolean)).size;
    $("aiStatus").textContent = aiState.enabled ? `AI architekt · ${aiState.model}` : aiState.message || "AI architekt zatím není aktivovaný.";
    $("aiSources").textContent = count ? `Pro architekta vybráno podkladů: ${count}. Výběr změníš v Podkladech.` : "Nejprve vyber podklady pro architekta.";
    $("useRoomSources").hidden = count > 0 || !Object.keys(data.room.sources).length;
    $("useRoomSources").disabled = busy || loading || aiSending;
    const pending = pendingAI();
    const locked = !aiState.enabled || !count || busy || loading || aiSending || aiBlocked() || Boolean(pending);
    $("askArchitect").disabled = locked;
    $("generateProposal").disabled = locked || !draft.image_source_id || aiState.image_generation === false;
    $("checkAISend").hidden = !pending;
    $("checkAISend").disabled = aiSending;
    const conversation = $("aiConversation"); conversation.replaceChildren();
    for (const job of aiState.jobs || []) {
      const article = document.createElement("article"); article.className = "ai-exchange";
      const question = document.createElement("p"); question.textContent = "Ty: " + job.message;
      const answer = document.createElement("p"); answer.className = "ai-answer";
      answer.textContent = job.answer || ({queued:"Požadavek je připravený…",running:"Architekt pracuje…",
        delivery_unknown:"Výsledek vyžaduje ověření. Požadavek znovu neposílej.",result_ready:"Výsledek AI je zachovaný; dokonči jeho uložení.",
        not_started:"Požadavek se nespustil.",failed:"Model požadavek nedokončil. Nový pokus se automaticky nespustí.",no_image:"AI odpověděla, ale obrazový návrh nevytvořila."}[job.status] || "");
      article.append(question, answer);
      if (job.status === "no_image") {
        const notice = document.createElement("p"); notice.className = "stage-note";
        notice.textContent = "Obrazový návrh nevznikl. Další placený pokus se automaticky nespustí."; article.append(notice);
      }
      if (["delivery_unknown","result_ready"].includes(job.status)) {
        const button = document.createElement("button"); button.type = "button"; button.className = "secondary";
        button.textContent = "Ověřit původní výsledek";
        button.addEventListener("click", () => perform(async () => {
          await api("/api/interior/ai/recover", {project_id:scope.project, room_id:scope.room, request_id:job.id});
          await refreshAI();
        })); article.append(button);
      }
      const variants = Array.isArray(job.variant_ids) ? job.variant_ids : job.variant_id ? [job.variant_id] : [];
      for (const [index, id] of variants.entries()) {
        const button = document.createElement("button"); button.type = "button";
        button.textContent = "Otevřít AI návrh" + (variants.length > 1 ? ` ${index + 1}` : "");
        button.addEventListener("click", () => { if (!busy) { view = "gallery"; load({...scope, base:id}); } });
        article.append(button);
      }
      conversation.append(article);
    }
  }
  async function refreshAI() {
    if (!scope.room) return;
    const captured = context(), token = aiLoader.begin();
    try {
      const state = await api("/api/interior/ai/status?" + new URLSearchParams({project_id:captured.project,room_id:captured.room,base_id:captured.base}));
      if (!aiLoader.current(token) || scopeKey(captured) !== scopeKey(scope)) return;
      aiState = state;
      const pending = pendingAI();
      if (pending && state.jobs.some(job => job.client_request_id === pending.request_id)) localStorage.removeItem(pendingAIKey());
      renderAI();
    } catch (_) {
      if (scopeKey(captured) === scopeKey(scope)) { aiState = {enabled:false,jobs:aiState.jobs || [],message:"Stav architekta se nepodařilo ověřit. Obnov stav před dalším odesláním."}; renderAI(); }
    }
  }
  async function submitAI(mode, previous = null) {
    if (aiSending || busy || loading || (!previous && aiBlocked())) return;
    aiSending = true; setBusy(true); renderAI();
    const captured = context();
    let payload = previous;
    try {
      if (!payload) {
        const message = $("aiText").value.trim() || (mode === "image" ? draft.prompt.trim() : "");
        if (!message) throw new Error("Napiš otázku nebo požadovanou změnu pro architekta.");
        await save();
        payload = {project_id:captured.project,room_id:captured.room,base_id:captured.base,expected_revision:revision,
          request_id:crypto.randomUUID(),message,mode};
        localStorage.setItem(pendingAIKey(captured), JSON.stringify(payload));
      }
      await api("/api/interior/ai/start", payload);
      if (scopeKey(captured) === scopeKey(scope)) {
        $("aiText").value = ""; stash(); await refreshAI();
      }
    } catch (error) {
      if (error.code === "request_rejected") localStorage.removeItem(pendingAIKey(captured));
      if (scopeKey(captured) === scopeKey(scope)) status(error.message, true);
    } finally { aiSending = false; setBusy(false); if (scopeKey(captured) === scopeKey(scope)) renderAI(); }
  }
  function renderSources() {
    $("sourceList").innerHTML = Object.values(data.room.sources).map(source => '<article class="source-card"><img src="' +
      escape(sourceUrl(source.id, "thumbnail")) + '" alt="' + escape(source.title) + '"><h3>' + escape(source.title) +
      '</h3><p class="muted">' + kindName[source.kind] + '</p><label><input type="checkbox" data-source="' + source.id + '"' +
      (draft.source_ids.includes(source.id) ? " checked" : "") + '>Použít pro tento návrh</label><label><input type="radio" name="workingImage" data-working="' + source.id + '"' +
      (draft.image_source_id === source.id ? " checked" : "") + '>Pracovní obrázek</label><a target="_blank" rel="noopener" href="' +
      escape(sourceUrl(source.id, "original")) + '">Otevřít originál</a></article>').join("") ||
      '<p class="muted">Přidej fotografie skutečného stavu, náčrt nebo inspiraci.</p>';
    $("sourceList").querySelectorAll("[data-source]").forEach(el => el.addEventListener("change", () => {
      if (busy) { renderSources(); return; }
      if (el.dataset.source === draft.image_source_id && !el.checked) { el.checked = true; status("Nejprve zvol jiný pracovní obrázek.", true); return; }
      draft.source_ids = el.checked ? [...draft.source_ids, el.dataset.source] : draft.source_ids.filter(id => id !== el.dataset.source);
      changed();
    }));
    $("sourceList").querySelectorAll("[data-working]").forEach(el => el.addEventListener("change", () => {
      if (busy) { renderSources(); return; }
      if (draft.image_source_id !== el.dataset.working && draft.annotations.length && !confirm("Změna pracovního obrázku odstraní kresbu pouze z rozpracované úpravy. Uložené varianty zůstanou zachované. Pokračovat?")) { renderSources(); return; }
      if (draft.image_source_id !== el.dataset.working) draft.annotations = [];
      draft.image_source_id = el.dataset.working;
      if (!draft.source_ids.includes(draft.image_source_id)) draft.source_ids.push(draft.image_source_id);
      changed(); renderSources();
    }));
  }
  function bindDrawing(area) {
    let stroke = null, path = null;
    const point = event => { const b = area.getBoundingClientRect(); return [Math.max(0,Math.min(1,(event.clientX-b.left)/b.width)), Math.max(0,Math.min(1,(event.clientY-b.top)/b.height))]; };
    area.addEventListener("pointerdown", event => {
      if (busy || event.button !== 0) return;
      if (draft.annotations.length >= 100) { status("Dosáhla jsi limitu 100 tahů.", true); return; }
      const total = draft.annotations.reduce((n,s) => n+s.length,0);
      if (total >= 4998) { status("Kresba má příliš mnoho bodů. Vrať poslední tah.", true); return; }
      event.preventDefault(); area.setPointerCapture(event.pointerId); stroke = [point(event)];
      path = document.createElementNS("http://www.w3.org/2000/svg", "path"); area.querySelector("svg").appendChild(path);
    });
    area.addEventListener("pointermove", event => {
      if (!stroke || stroke.length >= 1000 || draft.annotations.reduce((n,s)=>n+s.length,0)+stroke.length >= 5000) return;
      stroke.push(point(event)); path.setAttribute("d", stroke.map((p,i)=>(i?"L":"M")+p.map(n=>Math.round(n*1000)).join(" ")).join(" "));
    });
    function finish() { if (!stroke) return; if (stroke.length < 2) stroke.push(stroke[0]); draft.annotations.push(stroke); stroke = null; changed(); }
    area.addEventListener("pointerup", finish); area.addEventListener("pointercancel", finish);
  }
  async function save() {
    const captured = context(), sent = JSON.parse(JSON.stringify(draft));
    const outcome = await mutate("save_draft", {base_id: captured.base, expected_revision: revision, draft: sent}, captured);
    if (scopeKey(captured) === scopeKey(scope)) {
      revision = outcome.revision; dirty = JSON.stringify(sent) !== JSON.stringify(draft); stash();
      serverDraft = {...sent, revision};
      $("serverComparison").hidden = !dirty;
      $("draftStatus").textContent = dirty ? "Další změny zatím nejsou uložené." : "Rozpracováno uložené · verze " + revision;
    }
    return outcome;
  }
  function dataUrl(file) {
    return new Promise((resolve,reject) => { const reader = new FileReader(); reader.onerror = () => reject(new Error("Soubor se nepodařilo načíst."));
      reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.readAsDataURL(file); });
  }
  $("projectSelect").addEventListener("change", () => { if (!busy) { view = "gallery"; load({project: $("projectSelect").value, room: "", base: "base"}); } });
  $("roomSelect").addEventListener("change", () => { if (!busy) { view = "gallery"; load({...scope, room: $("roomSelect").value, base: "base"}); } });
  function create(mode) {
    if (busy) return; createMode = mode; $("createTitle").textContent = mode === "project" ? "Nový projekt" : "Nová místnost";
    $("projectNameLabel").hidden = mode !== "project"; $("createDialog").showModal();
  }
  $("newProject").addEventListener("click", () => create("project"));
  $("firstProject").addEventListener("click", () => create("project"));
  $("newRoom").addEventListener("click", () => create("room"));
  $("cancelCreate").addEventListener("click", () => $("createDialog").close());
  $("createForm").addEventListener("submit", event => { event.preventDefault(); perform(async () => {
    const outcome = createMode === "project" ? await mutate("create_project", {title: $("projectName").value, room_title: $("roomName").value}) :
      await mutate("create_room", {title: $("roomName").value});
    $("createDialog").close(); view = "gallery"; await load({project: outcome.project_id, room: outcome.room_id, base: "base"});
  }); });
  $("newVariant").addEventListener("click", () => { if (!busy) { view = "edit"; drawing = false; comparing = false; load({...scope, base: "base"}); } });
  $("openSources").addEventListener("click", () => { if (busy) return; returnView = view === "sources" ? returnView : view; view = "sources"; stash(); render(); });
  function back() { if (busy) return; view = view === "sources" ? returnView : "gallery"; drawing = false; render(); }
  $("backToGallery").addEventListener("click", back); $("closeSources").addEventListener("click", back);
  $("toggleNotes").addEventListener("click", () => { notesOpen = !notesOpen; render(); });
  $("editVariant").addEventListener("click", () => { if (busy) return; view = "edit"; comparing = false; render(); });
  $("compare").addEventListener("click", () => { comparing = !comparing; render(); });
  $("refresh").addEventListener("click", () => load());
  $("draw").addEventListener("click", () => { if (busy) return; drawing = !drawing; renderPicture(); });
  $("undo").addEventListener("click", () => { if (busy) return; draft.annotations.pop(); changed(); renderPicture(); });
  $("takeServerDraft").addEventListener("click", () => {
    if (busy || !serverDraft || !confirm("Nahradit neuložené změny posledním uloženým zadáním? Před potvrzením si můžeš vlastní text zkopírovat.")) return;
    const restored = restoreDraft(serverDraft, null);
    draft = restored.draft; revision = restored.revision; dirty = false; drawing = false; stash(); render();
    status("Načtené poslední uložené zadání.");
  });
  [["draftTitle","title"],["draftPrompt","prompt"],["draftFixed","fixed_elements"]].forEach(([id,key]) => $(id).addEventListener("input", () => { draft[key] = $(id).value; changed(); }));
  $("draftForm").addEventListener("submit", event => { event.preventDefault(); perform(async () => { await save(); status("Rozpracované zadání je uložené."); }); });
  $("saveSourceSelection").addEventListener("click", () => perform(async () => { await save(); status("Výběr podkladů je uložený."); }));
  $("saveVariant").addEventListener("click", () => perform(async () => {
    if (!draft.title.trim()) throw new Error("Nejprve návrh pojmenuj.");
    await save();
    const outcome = await mutate("create_variant", {base_id: scope.base, expected_revision: revision});
    view = "gallery"; drawing = false; await load({...scope, base: outcome.variant_id});
    status("Uložená nová varianta zadání. Původní návrh zůstal zachovaný.");
  }));
  $("noteForm").addEventListener("submit", event => { event.preventDefault(); perform(async () => {
    const text = $("noteText").value; if (!text.trim()) return;
    await mutate("add_note", {base_id: scope.base, text}); $("noteText").value = ""; await load(); status("Poznámka je uložená.");
  }); });
  $("noteText").addEventListener("input", stash);
  $("aiText").addEventListener("input", stash);
  $("aiForm").addEventListener("submit", event => { event.preventDefault(); submitAI("chat"); });
  $("generateProposal").addEventListener("click", () => submitAI("image"));
  $("checkAISend").addEventListener("click", () => { const pending = pendingAI(); if (pending) submitAI(pending.mode, pending); });
  $("useRoomSources").addEventListener("click", () => perform(async () => {
    const ids = Object.keys(data.room.sources);
    if (!ids.length || ids.length > 6) throw new Error("V Podkladech vyber nejvýše šest obrázků.");
    draft.source_ids = ids;
    if (!draft.image_source_id) draft.image_source_id = ids.find(id => data.room.sources[id].kind === "photo") || ids[0];
    changed(); await save(); render(); status("Podklady pro architekta jsou vybrané.");
  }));
  $("sourceFiles").addEventListener("change", () => { selectedFiles = [...$("sourceFiles").files]; });
  $("dropzone").addEventListener("dragover", event => { event.preventDefault(); $("dropzone").classList.add("dragging"); });
  $("dropzone").addEventListener("dragleave", () => $("dropzone").classList.remove("dragging"));
  $("dropzone").addEventListener("drop", event => { event.preventDefault(); if (busy) return; selectedFiles = [...event.dataTransfer.files]; $("dropzone").classList.remove("dragging"); status("Vybrané podklady: " + selectedFiles.map(f=>f.name).join(", ")); });
  $("uploadForm").addEventListener("submit", event => { event.preventDefault(); perform(async () => {
    if (!selectedFiles.length) throw new Error("Vyber fotografie nebo náčrty.");
    const captured = context(), files = [...selectedFiles], kind = $("sourceKind").value;
    let completed = 0;
    try {
      for (const file of files) {
        if (!file.size || file.size > 6 * 1024 * 1024) throw new Error(file.name + ": soubor musí být nejvýše 6 MiB.");
        status("Ukládám " + file.name + "…");
        await mutate("add_source", {title: file.name, kind, data: await dataUrl(file)}, captured); completed++;
      }
      selectedFiles = []; $("sourceFiles").value = ""; await load(captured); status("Podklady uložené: " + completed + ". Vyber pracovní obrázek.");
    } catch (error) {
      selectedFiles = files.slice(completed); await load(captured);
      throw new Error("Ověřeně uložené podklady: " + completed + ". " + error.message + " Před dalším pokusem ověř seznam.");
    }
  }); });
  $("fullscreen").addEventListener("click", async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch (_) { status("Ateliér vyplňuje okno. Pro celou obrazovku můžeš použít také zelené tlačítko okna Safari."); }
  });
  let initial;
  try { initial = JSON.parse(localStorage.getItem("samantha-interior-selection-v1") || "null"); } catch (_) {}
  load(initial && typeof initial.project === "string" && typeof initial.room === "string" ? {...initial, base: initial.base || "base"} : scope);
  root.setInterval(() => { if (scope.room && notesOpen && !aiSending && !loading && !busy) refreshAI(); }, 5000);
})(globalThis);
