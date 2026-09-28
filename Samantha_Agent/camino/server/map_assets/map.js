"use strict";
(() => {
  const el = id => document.getElementById(id);
  const status = el("status"), day = el("day");
  const palette = ["#546a51", "#765884", "#276d86", "#96552e", "#8b6a17"];
  let map, layer, tiles, points = [], timer, active = false, controller, generation = 0;
  let framed = false;

  function selected() { return points.filter(p => !day.value || p.day === day.value); }
  function clear() {
    points = [];
    if (map) { map.closePopup(); layer.clearLayers(); }
    el("points").replaceChildren();
    day.replaceChildren(new Option("Celá cesta", ""));
  }
  function label(p) {
    const date = p.day === "unknown" ? "Den pořízení neznámý" : p.day.split("-").reverse().join(". ");
    return `${p.title || "Okamžik"} · ${date} ${p.time} · ±${Math.round(p.accuracy_m)} m${p.uncertain ? " · nejistý čas" : ""}${p.accuracy_m > 100 ? " · přibližná poloha" : ""}`;
  }
  function link(p) {
    const a = document.createElement("a");
    a.href = p.href; a.textContent = label(p);
    return a;
  }
  function fit() {
    const visible = selected();
    if (visible.length) {
      map.fitBounds(visible.map(p => [p.latitude, p.longitude]), {padding: [25, 25], maxZoom: 15});
      framed = true;
      // No external requests before explicit consent AND a useful viewport.
      if (!map.hasLayer(tiles)) tiles.addTo(map);
    }
  }
  function render(reframe = false) {
    map.closePopup(); layer.clearLayers(); el("points").replaceChildren();
    const visible = selected(), days = [...new Set(points.map(p => p.day))].sort();
    const known = visible.filter(p => p.utc_ms !== null && !p.uncertain);
    const first = known[0], last = known[known.length - 1];
    const groups = new Map();
    let previous;
    for (const p of visible) {
      const color = palette[days.indexOf(p.day) % palette.length];
      if (previous && p.connect_previous && points.indexOf(p) === points.indexOf(previous) + 1) {
        L.polyline([[previous.latitude, previous.longitude], [p.latitude, p.longitude]],
          {color, weight: 3, dashArray: "6 8", interactive: false}).addTo(layer);
      }
      const key = `${p.latitude},${p.longitude}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(p);
      const item = document.createElement("li"); item.append(link(p)); el("points").append(item);
      previous = p;
    }
    for (const group of groups.values()) {
      const p = group[0], popup = document.createElement("div");
      const roles = [];
      if (group.includes(first)) roles.push("První známý bod");
      if (group.includes(last)) roles.push("Poslední známý bod (ne živá poloha)");
      const heading = document.createElement("strong");
      heading.textContent = roles.join(" · ") || "Místo záznamu"; popup.append(heading);
      for (const item of group) popup.append(link(item));
      const color = group.some(x => x.accuracy_m > 100) ? "#ad650d" : group.includes(last) ? "#2062ae" : group.includes(first) ? "#24753f" : "#546a51";
      L.circleMarker([p.latitude, p.longitude], {radius: group.length > 1 ? 9 : 7,
        color, fillColor: color, fillOpacity: .85, weight: 2}).bindPopup(popup).addTo(layer);
    }
    if (!visible.length) {
      if (map.hasLayer(tiles)) map.removeLayer(tiles);
      status.textContent = "Zatím tu nejsou dostupné GPS body pro tento výběr. Další mohou čekat v telefonu.";
    } else {
      if (reframe || !framed) fit();
      if (!map.hasLayer(tiles)) tiles.addTo(map);
      status.textContent = `${visible.length} míst záznamů · ověřeno ${new Date().toLocaleTimeString("cs-CZ")}. Další mohou čekat v telefonu.`;
    }
  }
  function stop() {
    generation++; clearTimeout(timer);
    if (controller) controller.abort();
    controller = null;
    clear();
    if (map && map.hasLayer(tiles)) map.removeLayer(tiles);
    el("refresh").disabled = false;
  }
  async function refresh() {
    if (!active || document.hidden || controller) return;
    clearTimeout(timer);
    const request = ++generation;
    controller = new AbortController();
    const current = controller;
    const timeout = setTimeout(() => current.abort(), 15000);
    el("refresh").disabled = true;
    try {
      const response = await fetch(document.body.dataset.mapUrl, {
        credentials: "same-origin", cache: "no-store", signal: current.signal,
        redirect: "error", headers: {Accept: "application/json"}
      });
      if (!response.ok) throw new Error("unavailable");
      const data = await response.json();
      if (request !== generation || document.hidden) return;
      const oldDay = day.value;
      points = data.points;
      day.replaceChildren(new Option("Celá cesta", ""));
      for (const date of [...new Set(points.map(p => p.day))].sort()) {
        day.append(new Option(date === "unknown" ? "Neznámý den pořízení" : date.split("-").reverse().join(". "), date));
      }
      day.value = [...day.options].some(o => o.value === oldDay) ? oldDay : "";
      render();
    } catch {
      if (request !== generation) return;
      clear();
      if (map.hasLayer(tiles)) map.removeLayer(tiles);
      status.textContent = "Mapu teď nelze ověřit. Staré body jsou skryté. Zkus Obnovit; při odvolaném přístupu se přihlas znovu ve Vieweru.";
    } finally {
      clearTimeout(timeout);
      if (request === generation) {
        controller = null; el("refresh").disabled = false;
        if (!document.hidden) timer = setTimeout(refresh, 60000);
      }
    }
  }
  el("open-map").addEventListener("click", () => {
    if (active) return;
    if (!window.L) { status.textContent = "Mapové rozhraní se nenačetlo. Obnov stránku."; return; }
    el("consent").hidden = true;
    for (const id of ["map", "map-controls", "legend", "point-list"]) el(id).hidden = false;
    map = L.map("map", {worldCopyJump: false}).setView([42, -5], 5);
    layer = L.layerGroup().addTo(map);
    tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, noWrap: true, referrerPolicy: "origin", crossOrigin: "anonymous",
      updateWhenIdle: true, keepBuffer: 0,
      attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
    });
    tiles.on("tileerror", () => {
      el("tile-status").textContent = "Část mapového podkladu se nenačetla. Body a odkazy do deníku zůstávají dostupné.";
    });
    active = true; refresh();
  });
  el("refresh").addEventListener("click", refresh);
  el("fit").addEventListener("click", fit);
  day.addEventListener("change", () => render(true));
  document.addEventListener("visibilitychange", () => {
    if (!active) return;
    if (document.hidden) { stop(); status.textContent = "Po návratu ověřím aktuální body."; }
    else refresh();
  });
  window.addEventListener("pagehide", stop);
  window.addEventListener("pageshow", () => { if (active) refresh(); });
})();
