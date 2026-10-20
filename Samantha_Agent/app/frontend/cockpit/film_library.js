(() => {
  "use strict";
  function create(root, options = {}) {
    const doc = options.document || document, request = options.fetch || ((...args) => fetch(...args));
    const editor = options.editor, confirmAction = options.confirm || (message => confirm(message));
    const every = options.setInterval || setInterval, stop = options.clearInterval || clearInterval;
    const node = id => root.querySelector(`#${id}`);
    const day = node("caminoFilmDay"), projects = node("caminoFilmProjects"), catalogStatus = node("caminoFilmCatalogStatus");
    const title = node("caminoFilmSelectedTitle"), status = node("caminoFilmStatus"), summary = node("caminoFilmSummary");
    const shots = node("caminoFilmShots"), createButton = node("caminoFilmCreateBtn"), refreshButton = node("caminoFilmRefreshBtn");
    const storageKey = "samantha.camino.film.selection";
    const validDate = value => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
    const validId = value => typeof value === "string" && /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(value);
    const dateLabel = value => { const [y, m, d] = value.split("-"); return `${Number(d)}. ${Number(m)}. ${y}`; };
    let selection = null, catalog = null, active = false, creating = false, epoch = 0, read = 0, catalogRead = 0, timer = null;
    function text(tag, value) { const n = doc.createElement(tag); n.textContent = value; return n; }
    function storage() { try { return options.storage || window.sessionStorage; } catch (_) { return null; } }
    function remember() { try { storage()?.setItem(storageKey, JSON.stringify(selection)); } catch (_) {} }
    function remembered() {
      try {
        const saved = JSON.parse(storage()?.getItem(storageKey) || "null");
        return saved && validDate(saved.local_date) && (saved.project_id === null || validId(saved.project_id)) ? saved : null;
      } catch (_) { return null; }
    }
    function clearSummary() {
      summary.textContent = ""; summary.classList.add("hidden"); shots.replaceChildren(); createButton.disabled = true;
    }
    function unavailable(message) {
      clearSummary(); projects.replaceChildren(); day.replaceChildren(); day.disabled = true;
      status.textContent = message; editor.suspend();
    }
    function canSwitch() {
      if (creating) { status.textContent = "Dokončuji uložení projektu. Před přepnutím počkej na výsledek."; return false; }
      return editor.canClose();
    }
    function renderCatalog() {
      day.replaceChildren(); projects.replaceChildren();
      for (const item of catalog.days) {
        const option = text("option", dateLabel(item.local_date)); option.value = item.local_date; day.appendChild(option);
      }
      day.disabled = creating || !catalog.days.length; day.value = selection?.local_date || "";
      for (const item of catalog.projects) {
        const li = text("li", ""), button = text("button", `Otevřít film ${dateLabel(item.local_date)} · revize ${item.revision} · hotové exporty ${item.ready_exports}`);
        button.type = "button"; button.className = "secondary"; button.disabled = creating;
        button.addEventListener("click", () => choose({local_date: item.local_date, project_id: item.project_id}));
        li.appendChild(button); projects.appendChild(li);
      }
      catalogStatus.textContent = catalog.days.length
        ? "Vyber uložený film nebo den z Macu. Před novým projektem se ověří zdroje a potvrdíš konečnost dat."
        : "Na Macu zatím není den s povolenými obrazovými zdroji pro film.";
      if (!catalog.projects.length) projects.appendChild(text("li", "Zatím není uložený ověřený filmový projekt."));
    }
    function renderDay(data) {
      clearSummary();
      if (!data.ok || data.local_date !== selection.local_date ||
          (selection.project_id && data.valid && data.project_id !== selection.project_id)) {
        unavailable("Vybraný projekt nelze bezpečně ověřit. Znovu načti přehled filmů."); return;
      }
      if (!data.valid) {
        if (data.exists) {
          catalog.projects = catalog.projects.filter(p => p.local_date !== selection.local_date);
          renderCatalog();
        }
        editor.close(); status.textContent = data.message || "Tento den zatím nemá ověřený projekt. Potvrď konečná data a ulož projekt.";
        createButton.disabled = creating; return;
      }
      if (!validId(data.project_id)) { unavailable("Projekt nemá platný identifikátor."); return; }
      selection.project_id = data.project_id; remember();
      renderCatalog();
      status.textContent = data.message || "Projekt je ověřený.";
      summary.textContent = `Uzavřené zdroje: ${data.photo_count} fotografií · ${data.video_count} celých videí · ${data.audio_count} zvukových voleb.`;
      summary.classList.remove("hidden");
      for (const shot of data.shots || []) shots.appendChild(text("li", `${shot.kind === "photo" ? "Fotografie" : "Video"} · ${shot.title || "Bez názvu"} · ${(shot.duration_ms / 1000).toLocaleString("cs-CZ")} s`));
      editor.open(data.project_id);
    }
    async function check() {
      if (!active || !selection || doc.hidden || creating) return;
      const current = epoch, serial = ++read, captured = {...selection};
      clearSummary(); status.textContent = "Ověřuji vybraný projekt a zdroje na Macu…";
      const params = new URLSearchParams({local_date: captured.local_date});
      if (captured.project_id) params.set("project_id", captured.project_id);
      try {
        const response = await request(`/api/camino/film/day?${params}`, {cache: "no-store"});
        const data = await response.json();
        if (current !== epoch || serial !== read || !active || doc.hidden) return;
        renderDay(data);
      } catch (_) {
        if (current === epoch && serial === read && active) unavailable("Projekt nelze nyní na Macu ověřit. Znovu načti přehled filmů.");
      }
    }
    async function choose(next, {initial = false} = {}) {
      const changed = selection?.local_date !== next.local_date || selection?.project_id !== next.project_id;
      if (!initial && changed && !canSwitch()) { day.value = selection?.local_date || ""; return false; }
      if (changed) { ++epoch; ++read; editor.close(); clearSummary(); }
      selection = {...next}; remember(); day.value = next.local_date;
      title.textContent = `Film z ${dateLabel(next.local_date)}`;
      await check(); return true;
    }
    async function refresh() {
      const current = epoch, serial = ++catalogRead;
      catalogStatus.textContent = "Načítám dny a uložené filmy…";
      try {
        const response = await request("/api/camino/film/catalog", {cache: "no-store"});
        const data = await response.json();
        if (current !== epoch || serial !== catalogRead || !active || doc.hidden) return;
        if (!data.ok || !Array.isArray(data.days) || !Array.isArray(data.projects) ||
            data.days.some(d => !validDate(d.local_date)) || data.projects.some(p => !validId(p.project_id) || !validDate(p.local_date))) throw new Error("invalid catalog");
        catalog = data;
        const saved = selection || remembered();
        let chosen = saved && catalog.projects.find(p => p.project_id === saved.project_id);
        if (saved?.project_id && !chosen && selection) {
          if (!editor.canClose()) {
            renderCatalog(); unavailable("Vybraný film není nyní v ověřeném přehledu. Obnov spojení a ulož rozpracované změny před přepnutím."); return;
          }
          editor.close(); selection = null;
        }
        chosen = chosen || (saved && catalog.days.some(d => d.local_date === saved.local_date) && {local_date: saved.local_date, project_id: null})
          || catalog.projects[0] || (catalog.days[0] && {...catalog.days[0], project_id: null});
        renderCatalog();
        if (chosen) await choose({local_date: chosen.local_date, project_id: chosen.project_id}, {initial: true});
        else { selection = null; editor.close(); clearSummary(); title.textContent = "Vybraný film"; status.textContent = "Vyber den po dokončení přenosu do Macu."; }
      } catch (_) {
        if (current === epoch && serial === catalogRead && active) {
          projects.replaceChildren(); day.replaceChildren(); day.disabled = true;
          catalogStatus.textContent = "Přehled filmů nelze nyní ověřit."; unavailable("Znovu načti přehled filmů. Rozpracované úpravy zůstávají v této kartě.");
        }
      }
    }
    async function createProject() {
      if (!selection || creating || !canSwitch()) return;
      const captured = {...selection};
      if (!confirmAction(`Potvrzuji, že všechna data a metadata dne ${dateLabel(captured.local_date)} jsou na Macu konečná. Uložit z nich filmový projekt?`)) return;
      const current = epoch; creating = true; ++read; clearSummary(); renderCatalog();
      status.textContent = "Kontroluji originály a ukládám projekt…";
      try {
        const response = await request("/api/camino/film/close-mac-day", {method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({local_date: captured.local_date, confirmed_final_mac_data: true})});
        const data = await response.json();
        if (current !== epoch || !active || doc.hidden) return;
        creating = false;
        if (data.ok) { renderDay(data); await refresh(); }
        else { status.textContent = data.message || "Projekt se nepodařilo uložit."; createButton.disabled = false; }
      } catch (_) {
        if (current === epoch && active) status.textContent = "Odpověď se ztratila. Znovu ověř přehled filmů před dalším uložením.";
      } finally { creating = false; if (catalog && active) renderCatalog(); }
    }
    day.addEventListener("change", () => {
      if (!catalog || !catalog.days.some(d => d.local_date === day.value)) return;
      const existing = catalog.projects.find(p => p.local_date === day.value);
      return choose({local_date: day.value, project_id: existing?.project_id || null});
    });
    createButton.addEventListener("click", createProject); refreshButton.addEventListener("click", refresh);
    doc.addEventListener("visibilitychange", () => {
      if (!active) return;
      if (doc.hidden) { ++read; ++catalogRead; clearSummary(); projects.replaceChildren(); day.replaceChildren(); day.disabled = true; }
      else refresh();
    });
    return {
      open() { active = true; stop(timer); timer = every(refresh, 60000); return refresh(); },
      close() { active = false; ++epoch; ++read; ++catalogRead; stop(timer); clearSummary(); editor.close(); },
      refresh, check, choose, createProject,
    };
  }
  window.SamanthaFilmLibrary = {create};
})();
