(() => {
  "use strict";
  const panel = document.getElementById("codexSessionsPanel");
  if (!panel) return;
  const list = document.getElementById("codexSessionsList");
  const status = document.getElementById("codexSessionsStatus");
  const refreshButton = document.getElementById("codexSessionsRefreshBtn");
  const screenList = document.getElementById("screenSessionsList");
  const screenStatus = document.getElementById("screenSessionsStatus");
  let busy = false;

  async function refreshScreens() {
    try {
      const response = await fetch("/api/screen/sessions", {cache: "no-store"});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Přehled screenů není dostupný.");
      screenList.replaceChildren();
      screenStatus.textContent = data.sessions.length
        ? `${data.sessions.length} screenů · ověřeno ${new Date(data.generated_at).toLocaleTimeString("cs-CZ")}`
        : "Žádný screen neběží.";
      for (const session of data.sessions) {
        const card = document.createElement("div");
        card.className = "recovery-card";
        const title = document.createElement("strong");
        title.textContent = session.socket;
        const details = document.createElement("p");
        const state = session.state === "Attached" ? "Připojený" : "Odpojený";
        details.textContent = `${state} · ${session.project} · běží ${session.age} · spuštěno ${session.started} · procesů uvnitř: ${session.process_count} · Codex: ${session.codex_count}`;
        card.append(title, details);
        if (session.can_stop) {
          const stop = document.createElement("button");
          stop.type = "button";
          stop.className = "secondary danger";
          stop.textContent = session.force_available ? "Vynutit uzavření screenu" : "Uzavřít screen";
          stop.addEventListener("click", () => terminateScreen(session));
          card.append(stop);
        } else {
          const reason = document.createElement("p");
          reason.textContent = session.protected_reason;
          card.append(reason);
        }
        screenList.append(card);
      }
    } catch (error) {
      screenList.replaceChildren();
      screenStatus.textContent = error.message || "Přehled screenů se nepodařilo načíst.";
    }
  }

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
      await refreshScreens();
      busy = false;
      refreshButton.disabled = false;
    }
  }

  async function terminate(session) {
    if (busy) return;
    const action = session.force_available ? "Vynutit ukončení" : "Ukončit";
    if (!window.confirm(`${action} Codex na ${session.tty} (PID ${session.pid}, spuštěno ${session.started})?\nProbíhající odpověď se přeruší. Rozpracované soubory a screen zůstanou zachované.`)) return;
    busy = true;
    panel.querySelectorAll("button").forEach(button => { button.disabled = true; });
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

  async function terminateScreen(session) {
    if (busy) return;
    const action = session.force_available ? "Vynutit uzavření" : "Uzavřít";
    const warning = session.force_available
      ? "Nereagující screen bude vynuceně ukončen. Procesy uvnitř mohou zůstat běžet; potom zkontroluj přehled."
      : "Terminálová okna screenu se zavřou a práce uvnitř se může přerušit.";
    if (!window.confirm(`${action} screen ${session.socket} (spuštěno ${session.started}, procesů uvnitř: ${session.process_count})?\n${warning}\nSoubory se nemažou.`)) return;
    busy = true;
    panel.querySelectorAll("button").forEach(button => { button.disabled = true; });
    let message;
    try {
      const response = await fetch("/api/screen/sessions/stop", {
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
    screenStatus.textContent = message;
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
