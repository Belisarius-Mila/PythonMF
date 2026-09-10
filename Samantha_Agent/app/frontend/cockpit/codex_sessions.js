(() => {
  "use strict";
  const panel = document.getElementById("codexSessionsPanel");
  if (!panel) return;
  const list = document.getElementById("codexSessionsList");
  const status = document.getElementById("codexSessionsStatus");
  const refreshButton = document.getElementById("codexSessionsRefreshBtn");
  let busy = false;

  async function refresh() {
    if (busy) return;
    busy = true;
    refreshButton.disabled = true;
    try {
      const response = await fetch("/api/codex/sessions", {cache: "no-store"});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Přehled není dostupný.");
      list.replaceChildren();
      status.textContent = `${data.sessions.length} běžících relací · ověřeno ${new Date(data.generated_at).toLocaleTimeString("cs-CZ")}`;
      if (!data.sessions.length) status.textContent = "Žádná terminálová relace Codexu neběží.";
      for (const session of data.sessions) {
        const card = document.createElement("div");
        card.className = "recovery-card";
        const title = document.createElement("strong");
        title.textContent = `${session.tty} · ${session.label}`;
        const details = document.createElement("p");
        details.textContent = `${session.project} · běží ${session.age} · PID ${session.pid} · spuštěno ${session.started}`;
        card.append(title, details);
        if (session.can_stop) {
          const stop = document.createElement("button");
          stop.type = "button";
          stop.className = "secondary danger";
          stop.textContent = session.force_available ? "Vynutit ukončení" : "Ukončit relaci";
          stop.addEventListener("click", () => terminate(session));
          card.append(stop);
        } else {
          const reason = document.createElement("p");
          reason.textContent = session.protected_reason;
          card.append(reason);
        }
        list.append(card);
      }
    } catch (error) {
      list.replaceChildren();
      status.textContent = error.message || "Přehled se nepodařilo načíst.";
    } finally {
      busy = false;
      refreshButton.disabled = false;
    }
  }

  async function terminate(session) {
    if (busy) return;
    const action = session.force_available ? "Vynutit ukončení" : "Ukončit";
    if (!window.confirm(`${action} Codex na ${session.tty} (PID ${session.pid}, spuštěno ${session.started})?\nProbíhající odpověď se přeruší. Rozpracované soubory a screen zůstanou zachované.`)) return;
    busy = true;
    list.querySelectorAll("button").forEach(button => { button.disabled = true; });
    let message;
    try {
      const response = await fetch("/api/codex/sessions/stop", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({pid: session.pid, identity: session.identity,
          confirmed: true, force: Boolean(session.force_available)})
      });
      const data = await response.json();
      message = data.message || "Výsledek není známý; obnov přehled.";
    } catch (_) {
      message = "Spojení se přerušilo. Nejdřív ověř přehled; požadavek se automaticky neopakuje.";
    } finally {
      busy = false;
    }
    await refresh();
    status.textContent = message;
  }

  refreshButton.addEventListener("click", refresh);
  panel.addEventListener("toggle", () => { if (panel.open) refresh(); });
  document.getElementById("dashboardSessionsBtn").addEventListener("click", () => {
    panel.open = true;
    panel.scrollIntoView({behavior: "smooth", block: "start"});
    refresh();
  });
  window.setInterval(() => { if (panel.open && !document.hidden) refresh(); }, 10000);
})();
