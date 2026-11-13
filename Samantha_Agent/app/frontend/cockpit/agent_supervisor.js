(() => {
  "use strict";
  const states = {ok: "V pořádku", working: "Pracuje", warning: "Pozor", error: "Chyba",
    unknown: "Neověřeno", disabled: "Vypnuto", outside_hours: "Mimo provozní okno"};
  let pending = false;
  function time(value) {
    return value ? new Date(value).toLocaleString("cs-CZ", {timeZone: "Europe/Prague"}) : "zatím nedoloženo";
  }
  function render(data, status, list, doc = document) {
    list.replaceChildren();
    if (!data || !data.ok) {
      status.textContent = "Stav dohledu nelze ověřit. Poslední známý stav není potvrzením běhu.";
      return;
    }
    const mode = data.configured
      ? (data.worker_recent ? "Dohled se pravidelně ozývá." : "Dohled je zapnutý, jeho běh není čerstvě doložený.")
      : "Pravidelný dohled je vypnutý.";
    status.textContent = `${mode} Poslední kontrola: ${time(data.last_run_at)}. `
      + `Upozornění: ${data.notifications_enabled ? "zapnutá" : "vypnutá"}. `
      + "Vnější hlídání dostupnosti Macu není nastavené.";
    for (const item of data.rows || []) {
      const card = doc.createElement("div");
      card.className = "agent-supervisor-row";
      const title = doc.createElement("strong");
      title.textContent = `${item.label}: ${states[item.state] || "Neověřeno"}`;
      const reason = doc.createElement("div");
      reason.textContent = item.message;
      const dates = doc.createElement("div");
      dates.className = "project-meta";
      dates.textContent = `Poslední úspěch: ${time(item.last_success_at)} · Další termín: ${time(item.next_due_at)}`;
      card.append(title, reason, dates);
      list.appendChild(card);
    }
    const unknown = Number((data.notification_counts || {}).delivery_unknown || 0);
    if (unknown) status.textContent += ` U ${unknown} oznámení není doručení potvrzené; neposílají se znovu.`;
  }
  async function refresh() {
    const status = document.getElementById("agentSupervisorStatus");
    const list = document.getElementById("agentSupervisorList");
    if (!status || !list || pending) return;
    pending = true;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 6000);
    try {
      const response = await fetch("/api/agent-supervisor/status", {cache: "no-store", signal: controller.signal});
      const data = await response.json();
      render(response.ok ? data : {ok: false}, status, list);
    } catch (_) {
      render({ok: false}, status, list);
    } finally {
      window.clearTimeout(timer);
      pending = false;
    }
  }
  window.SamanthaAgentSupervisor = {refresh, render};
})();
