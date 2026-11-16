(() => {
  "use strict";
  const states = {pending: "Čeká na úklid", blocked: "Ponechaná", unclosed: "Neuzavřená"};
  let inFlight = false, generation = 0, pollTimer = null, initialized = false;
  function date(seconds) {
    return Number.isFinite(seconds) && seconds > 0
      ? new Date(seconds * 1000).toLocaleString("cs-CZ", {timeZone: "Europe/Prague"}) : "zatím nedoloženo";
  }
  function text(element, value) { if (element.textContent !== value) element.textContent = value; }
  function render(data, status, metrics, list, doc = document) {
    metrics.replaceChildren(); list.replaceChildren();
    status.className = "status-line";
    if (!data || !data.ok) {
      text(status, "Stav úklidu nelze ověřit. Obnov přehled.");
      status.className += " bad";
      return;
    }
    const audit = data.audit || {}, scheduler = data.scheduler || {}, run = data.last_run || {};
    let message = !data.enabled ? "Automatický úklid je vypnutý."
      : scheduler.loaded === true ? "Automatický úklid je zapnutý, kontrola probíhá každou hodinu."
      : scheduler.loaded === false ? "Úklid je povolený, služba ale není načtená."
      : "Úklid je povolený, stav plánovače zatím není ověřený.";
    if (scheduler.last_exit_code != null && scheduler.last_exit_code !== 0) message += " Poslední běh služby skončil chybou.";
    if (data.enabled && run.at && !run.recent) message += " Nový běh není čerstvě doložený.";
    if (run.state === "attention") message += " Poslední úklid vyžaduje kontrolu.";
    if (audit.pending) message += " Ověřuji pracovní kopie…";
    if (audit.failed) message += " Přehled kopií se nepodařilo obnovit.";
    if (audit.checked_at && audit.stale) message += " Zobrazené kopie jsou poslední známý stav.";
    text(status, message);
    function metric(label, value) {
      const row = doc.createElement("div"); row.className = "dashboard-row";
      const title = doc.createElement("span"); title.className = "dashboard-label"; title.textContent = label;
      const body = doc.createElement("span"); body.className = "dashboard-value"; body.textContent = value;
      row.append(title, body); metrics.appendChild(row);
    }
    metric("Poslední běh", date(run.at));
    const change = run.free_change_bytes;
    metric("Změna volného místa při běhu", Number.isFinite(change)
      ? `${change > 0 ? "+" : ""}${(change / 2 ** 30).toFixed(2)} GiB` : "neověřeno");
    metric("Odstraněno při běhu", run.at
      ? `${run.worktrees_removed ?? "?"} pracovních kopií · ${run.autosave_removed ?? "?"} autosave souborů` : "zatím nedoloženo");
    const counts = data.counts || {};
    metric("Pracovní kopie", Number.isInteger(counts.pending)
      ? `Čekající ${counts.pending} · Ponechané ${counts.blocked} · Neuzavřené ${counts.unclosed}` : "zatím neověřeno");
    metric("Přehled kopií ověřen", date(audit.checked_at));
    for (const item of data.rows || []) {
      const card = doc.createElement("div"); card.className = "agent-supervisor-row";
      const title = doc.createElement("strong"); title.textContent = `${states[item.state] || "Neověřeno"}: ${item.name}`;
      const reason = doc.createElement("div"); reason.textContent = item.reason;
      card.append(title, reason);
      if (item.ready_after && item.state === "pending") {
        const earliest = doc.createElement("div"); earliest.className = "project-meta";
        earliest.textContent = `Nejdřívější úklid: ${date(item.ready_after)}`; card.appendChild(earliest);
      }
      list.appendChild(card);
    }
    if (audit.checked_at && !data.rows?.length) {
      const empty = doc.createElement("p"); empty.className = "project-meta";
      empty.textContent = "Žádné dočasné pracovní kopie v povoleném rozsahu."; list.appendChild(empty);
    }
  }
  function visible() {
    return !document.hidden && document.getElementById("servicePanel")?.open
      && document.getElementById("serviceOperationsPanel")?.open;
  }
  async function refresh(force = false) {
    if (inFlight || !visible()) return;
    const status = document.getElementById("housekeepingStatus"), metrics = document.getElementById("housekeepingMetrics");
    const list = document.getElementById("housekeepingList"), button = document.getElementById("housekeepingRefreshBtn");
    if (!status || !metrics || !list || !button) return;
    inFlight = true; button.disabled = true;
    const token = ++generation, controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 6000);
    window.clearTimeout(pollTimer);
    let auditPending = false;
    try {
      const response = await fetch(`/api/workspace-housekeeping${force === true ? "?refresh=1" : ""}`, {cache: "no-store", signal: controller.signal});
      const data = await response.json();
      if (token !== generation || !visible()) return;
      render(response.ok ? data : {ok: false}, status, metrics, list);
      auditPending = Boolean(data.ok && data.audit?.pending);
      if (auditPending) pollTimer = window.setTimeout(() => refresh(), 1000);
    } catch (_) {
      if (token === generation && visible()) render({ok: false}, status, metrics, list);
    } finally {
      window.clearTimeout(timeout); inFlight = false; button.disabled = auditPending;
      if (token !== generation && visible()) pollTimer = window.setTimeout(() => refresh(), 0);
    }
  }
  function init() {
    if (initialized) return;
    initialized = true;
    document.getElementById("housekeepingRefreshBtn")?.addEventListener("click", () => refresh(true));
    for (const id of ["servicePanel", "serviceOperationsPanel"]) {
      document.getElementById(id)?.addEventListener("toggle", () => {
        if (visible()) refresh(); else { generation++; window.clearTimeout(pollTimer); }
      });
    }
    document.addEventListener("visibilitychange", () => {
      if (visible()) refresh(); else { generation++; window.clearTimeout(pollTimer); }
    });
    window.setInterval(() => { if (visible()) refresh(); }, 60000);
    if (visible()) refresh();
  }
  window.SamanthaWorkspaceHousekeeping = {init, refresh, render};
})();
