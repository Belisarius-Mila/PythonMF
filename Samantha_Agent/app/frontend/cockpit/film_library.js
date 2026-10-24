(() => {
  "use strict";
  function create(root, options = {}) {
    const doc = options.document || document, request = options.fetch || ((...args) => fetch(...args));
    const editor = options.editor, confirmAction = options.confirm || (message => confirm(message));
    const every = options.setInterval || setInterval, stop = options.clearInterval || clearInterval;
    const node = id => root.querySelector(`#${id}`);
    const trip = node("caminoFilmTrip"), day = node("caminoFilmDay"), projects = node("caminoFilmProjects");
    const catalogStatus = node("caminoFilmCatalogStatus"), title = node("caminoFilmSelectedTitle");
    const status = node("caminoFilmStatus"), summary = node("caminoFilmSummary"), shots = node("caminoFilmShots");
    const createButton = node("caminoFilmCreateBtn"), refreshButton = node("caminoFilmRefreshBtn");
    const storageKey = "samantha.camino.film.selection.v2";
    const validDate = value => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
    const validId = value => typeof value === "string" && /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(value);
    const dateLabel = value => { const [y, m, d] = value.split("-"); return `${Number(d)}. ${Number(m)}. ${y}`; };
    let selection = null, catalog = null, journeys = null, active = false, creating = false;
    let epoch = 0, read = 0, catalogRead = 0, timer = null;
    function text(tag, value) { const n = doc.createElement(tag); n.textContent = value; return n; }
    function storage() { try { return options.storage || window.sessionStorage; } catch (_) { return null; } }
    function remember() { try { storage()?.setItem(storageKey, JSON.stringify(selection)); } catch (_) {} }
    function remembered() {
      try {
        const saved = JSON.parse(storage()?.getItem(storageKey) || "null");
        return saved && validId(saved.trip_id) && (saved.local_date === null || validDate(saved.local_date)) &&
          (saved.project_id === null || validId(saved.project_id)) ? saved : null;
      } catch (_) { return null; }
    }
    function selectedTrip() { return journeys?.trips.find(t => t.id === selection?.trip_id); }
    function tripLabel(item) {
      const period = [item.start_date, item.end_date].filter(Boolean).join(" – ");
      const duplicate = journeys.trips.filter(t => t.name === item.name).length > 1;
      return item.name + (period ? ` · ${period}` : "") + (item.status === "archived" ? " · archiv" : "") +
        (duplicate ? ` · ${item.id.slice(-8)}` : "");
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
    function renderTrips() {
      trip.replaceChildren();
      for (const item of journeys?.trips || []) {
        const option = text("option", tripLabel(item)); option.value = item.id; trip.appendChild(option);
      }
      trip.disabled = creating || !journeys?.trips.length; trip.value = selection?.trip_id || "";
    }
    function renderCatalog() {
      renderTrips(); day.replaceChildren(); projects.replaceChildren();
      for (const item of catalog?.days || []) {
        const option = text("option", dateLabel(item.local_date)); option.value = item.local_date; day.appendChild(option);
      }
      day.disabled = creating || !catalog?.days.length; day.value = selection?.local_date || "";
      for (const item of catalog?.projects || []) {
        const li = text("li", ""), button = text("button", `Otevřít film ${dateLabel(item.local_date)} · revize ${item.revision} · hotové exporty ${item.ready_exports}`);
        button.type = "button"; button.className = "secondary"; button.disabled = creating;
        button.addEventListener("click", () => choose({...item, trip_id: selection.trip_id}));
        li.appendChild(button); projects.appendChild(li);
      }
      catalogStatus.textContent = catalog?.days.length
        ? "Vyber uložený film nebo den vybrané cesty. Před novým filmem potvrdíš konečnost dat na Macu."
        : "Vybraný projekt zatím nemá den s povolenými obrazovými zdroji pro film.";
      if (!catalog?.projects.length) projects.appendChild(text("li", "Zatím není uložený ověřený filmový projekt."));
    }
    function renderDay(data) {
      clearSummary();
      if (!data.ok || data.trip_id !== selection.trip_id || data.local_date !== selection.local_date ||
          (selection.project_id && data.valid && data.project_id !== selection.project_id)) {
        unavailable("Vybraný projekt nelze bezpečně ověřit. Znovu načti přehled filmů."); return;
      }
      if (!data.valid) {
        if (data.exists) {
          catalog.projects = catalog.projects.filter(p => p.local_date !== selection.local_date); renderCatalog();
        }
        editor.close(); status.textContent = data.message || "Tento den zatím nemá ověřený film. Potvrď konečná data a ulož projekt.";
        createButton.disabled = creating; return;
      }
      if (!validId(data.project_id)) { unavailable("Projekt nemá platný identifikátor."); return; }
      selection.project_id = data.project_id; remember(); renderCatalog();
      status.textContent = data.message || "Projekt je ověřený.";
      summary.textContent = `Uzavřené zdroje: ${data.photo_count} fotografií · ${data.video_count} celých videí · ${data.audio_count} zvukových voleb.`;
      summary.classList.remove("hidden");
      for (const shot of data.shots || []) shots.appendChild(text("li", `${shot.kind === "photo" ? "Fotografie" : "Video"} · ${shot.title || "Bez názvu"} · ${(shot.duration_ms / 1000).toLocaleString("cs-CZ")} s`));
      editor.open(data.project_id);
    }
    async function check() {
      if (!active || !validDate(selection?.local_date) || doc.hidden || creating) return;
      const current = epoch, serial = ++read, captured = {...selection};
      clearSummary(); status.textContent = "Ověřuji vybraný projekt a zdroje na Macu…";
      const params = new URLSearchParams({trip_id: captured.trip_id, local_date: captured.local_date});
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
      if (!validId(next.trip_id) || next.trip_id !== selection?.trip_id || !validDate(next.local_date) ||
          !(next.project_id === null || validId(next.project_id))) return false;
      const changed = selection?.local_date !== next.local_date || selection?.project_id !== next.project_id;
      if (!initial && changed && !canSwitch()) { day.value = selection?.local_date || ""; return false; }
      if (changed) { ++epoch; ++read; editor.close(); clearSummary(); }
      selection = {trip_id: next.trip_id, local_date: next.local_date, project_id: next.project_id};
      remember(); day.value = next.local_date;
      title.textContent = `${selectedTrip()?.name || "Projekt"} · Film z ${dateLabel(next.local_date)}`;
      await check(); return true;
    }
    async function refresh() {
      const current = epoch, serial = ++catalogRead;
      catalogStatus.textContent = "Načítám projekty, dny a uložené filmy…";
      try {
        const response = await request("/api/camino/film/trips", {cache: "no-store"});
        const data = await response.json();
        if (current !== epoch || serial !== catalogRead || !active || doc.hidden) return;
        if (!data.ok || !Array.isArray(data.trips) || !validId(data.default_trip_id) ||
            new Set(data.trips.map(t => t.id)).size !== data.trips.length ||
            data.trips.some(t => !validId(t.id) || typeof t.name !== "string" || !["active", "archived"].includes(t.status))) throw new Error("invalid trips");
        journeys = data;
        const saved = selection || remembered();
        const tripId = saved?.trip_id || data.default_trip_id;
        if (!data.trips.some(t => t.id === tripId)) {
          unavailable("Vybraná cesta není v Mac archivu. Vyber jiný projekt."); renderTrips(); return;
        }
        const catalogResponse = await request(`/api/camino/film/catalog?trip_id=${tripId}`, {cache: "no-store"});
        const next = await catalogResponse.json();
        if (current !== epoch || serial !== catalogRead || !active || doc.hidden) return;
        if (!next.ok || next.trip_id !== tripId || !Array.isArray(next.days) || !Array.isArray(next.projects) ||
            next.days.some(d => !validDate(d.local_date)) || next.projects.some(p => !validId(p.project_id) || !validDate(p.local_date))) throw new Error("invalid catalog");
        catalog = next;
        let chosen = saved && catalog.projects.find(p => p.project_id === saved.project_id);
        if (saved?.project_id && !chosen && selection) {
          if (!editor.canClose()) {
            renderCatalog(); unavailable("Vybraný film není nyní v ověřeném přehledu. Obnov spojení a ulož rozpracované změny před přepnutím."); return;
          }
          editor.close();
        }
        chosen = chosen || (saved && catalog.days.some(d => d.local_date === saved.local_date) && {local_date: saved.local_date, project_id: null})
          || catalog.projects[0] || (catalog.days[0] && {...catalog.days[0], project_id: null});
        selection = {trip_id: tripId, local_date: saved?.local_date || null, project_id: saved?.project_id || null};
        renderCatalog();
        if (chosen) await choose({...chosen, trip_id: tripId}, {initial: true});
        else {
          selection = {trip_id: tripId, local_date: null, project_id: null}; remember(); editor.close(); clearSummary();
          title.textContent = selectedTrip().name; status.textContent = "Vyber den po dokončení přenosu do Macu.";
        }
      } catch (_) {
        if (current === epoch && serial === catalogRead && active) {
          trip.replaceChildren(); trip.disabled = true;
          catalogStatus.textContent = "Přehled filmů nelze nyní ověřit."; unavailable("Znovu načti přehled filmů. Rozpracované úpravy zůstávají v této kartě.");
        }
      }
    }
    async function chooseTrip(tripId) {
      if (!journeys?.trips.some(t => t.id === tripId)) return false;
      if (tripId === selection?.trip_id) return true;
      if (!canSwitch()) { trip.value = selection?.trip_id || ""; return false; }
      ++epoch; ++read; ++catalogRead; editor.close(); clearSummary();
      catalog = null; selection = {trip_id: tripId, local_date: null, project_id: null}; remember(); renderCatalog();
      await refresh(); return true;
    }
    async function createProject() {
      if (!validDate(selection?.local_date) || creating || !canSwitch()) return;
      const captured = {...selection};
      if (!confirmAction(`Potvrzuji, že všechna data a metadata projektu ${selectedTrip().name} dne ${dateLabel(captured.local_date)} jsou na Macu konečná. Uložit z nich filmový projekt?`)) return;
      const current = epoch; creating = true; ++read; clearSummary(); renderCatalog();
      status.textContent = "Kontroluji originály a ukládám projekt…";
      try {
        const response = await request("/api/camino/film/close-mac-day", {method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({trip_id: captured.trip_id, local_date: captured.local_date, confirmed_final_mac_data: true})});
        const data = await response.json();
        if (current !== epoch || !active || doc.hidden) return;
        creating = false;
        if (data.ok) { renderDay(data); await refresh(); }
        else { status.textContent = data.message || "Projekt se nepodařilo uložit."; createButton.disabled = false; }
      } catch (_) {
        if (current === epoch && active) status.textContent = "Odpověď se ztratila. Znovu ověř přehled filmů před dalším uložením.";
      } finally { creating = false; if (catalog && active) renderCatalog(); }
    }
    trip.addEventListener("change", () => chooseTrip(trip.value));
    day.addEventListener("change", () => {
      if (!catalog || !catalog.days.some(d => d.local_date === day.value)) return;
      const existing = catalog.projects.find(p => p.local_date === day.value);
      return choose({trip_id: selection.trip_id, local_date: day.value, project_id: existing?.project_id || null});
    });
    createButton.addEventListener("click", createProject); refreshButton.addEventListener("click", refresh);
    doc.addEventListener("visibilitychange", () => {
      if (!active) return;
      if (doc.hidden) { ++read; ++catalogRead; clearSummary(); projects.replaceChildren(); day.replaceChildren(); day.disabled = true; trip.replaceChildren(); trip.disabled = true; }
      else refresh();
    });
    return {
      open() { active = true; stop(timer); timer = every(refresh, 60000); return refresh(); },
      close() { active = false; ++epoch; ++read; ++catalogRead; stop(timer); clearSummary(); editor.close(); },
      refresh, check, choose, chooseTrip, createProject,
    };
  }
  window.SamanthaFilmLibrary = {create};
})();
