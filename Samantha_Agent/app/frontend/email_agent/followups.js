(() => {
  "use strict";
  const endpoint = "/api/email-agent/followups";
  const storageKey = "samantha.email.followup.intent.v1";
  const byId = id => document.getElementById(id);
  const dialog = byId("followupEditor"), form = byId("followupForm");
  const status = byId("followupsStatus"), error = byId("followupError");
  const fields = {title: byId("followupTitle"), goal: byId("followupGoal"),
    next_step: byId("followupNextStep"), waiting_on: byId("followupWaitingOn"),
    check_at: byId("followupCheckAt")};
  const records = new Map(), cards = new Map();
  let editing = null, pending = null, storageFault = false;
  let busy = false, ready = false, sequence = 0, epoch = 0;
  const node = (tag, text, className) => {
    const value = document.createElement(tag);
    if (text !== undefined) value.textContent = text;
    if (className) value.className = className;
    return value;
  };
  const dateText = instant => new Date(instant).toLocaleString("cs-CZ", {timeZone: "Europe/Prague"});
  const waitingText = {me: "Je řada na mně", other: "Čekáme na druhou stranu",
    review: "Zpráva ke kontrole", unknown: "Další postup není určený"};
  const checkText = {source_binding_unverified: "Vazbu původního e-mailu je potřeba ověřit.",
    binding_review: "Přišla možná související zpráva. Přiřazení vyžaduje ruční kontrolu.",
    source_unverified: "Kontrolu nelze dokončit. Zdroj není úplně dočtený nebo dostatečně čerstvý.",
    related_message: "Je dostupná doložená související zpráva. Posuď další krok.",
    due_no_observed_reply: "Čas kontroly nastal. Ve sledovaném dočteném zdroji nebyla nalezena doložená odpověď.",
    waiting: "Zdroj ověřený. Čas plánované kontroly ještě nenastal."};
  try {
    const saved = window.sessionStorage.getItem(storageKey);
    if (saved) {
      pending = JSON.parse(saved);
      if (!pending || !/^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$/.test(pending.operation_id)
          || !(typeof pending.source_item_id === "string" && /^[a-f0-9]{64}$/.test(pending.source_item_id)
            || typeof pending.id === "string" && /^[a-f0-9]{32}$/.test(pending.id))) throw new Error();
    }
  } catch (_) { storageFault = true; }

  function controls() {
    const locked = busy || Boolean(pending) || storageFault;
    byId("followupSave").disabled = locked || !ready || Boolean(editing?.conflict);
    byId("followupCancel").disabled = busy;
    byId("followupVerify").hidden = !pending && !storageFault;
    byId("followupVerify").disabled = busy;
    for (const [key, input] of Object.entries(fields)) {
      input.disabled = locked || (editing?.mode === "reopen" && key !== "check_at");
    }
  }
  function button(label, callback, selected = false) {
    const value = node("button", label, selected ? "" : "secondary");
    value.type = "button";
    value.disabled = busy || Boolean(pending) || storageFault || !ready || selected;
    if (["Hlídání", "Vyřízeno"].includes(label)) value.setAttribute("aria-pressed", String(selected));
    value.addEventListener("click", async () => {
      if (busy || pending || storageFault || !ready || selected) return;
      try { await callback(); }
      catch (exc) { status.textContent = exc.message; }
    });
    return value;
  }
  function close() {
    if (busy) return;
    dialog.close(); editing = null; epoch++;
    return refresh();
  }
  function open(mode, source) {
    if (busy || pending || storageFault || !ready) return;
    epoch++;
    editing = {mode, source};
    const initial = mode === "create" ? {
      title: source.proposal?.metadata?.title || source.header?.subject || "",
      goal: source.proposal?.summary || "", next_step: "", waiting_on: "unknown", check_at: "",
    } : source;
    for (const [key, input] of Object.entries(fields)) {
      input.value = key === "check_at" && initial[key]
        ? window.SamanthaFollowupTime.toInput(initial[key]) : initial[key] || "";
    }
    error.textContent = mode === "reopen" ? "Potvrď nový budoucí čas kontroly. Cíl a historie zůstanou zachované."
      : mode === "create" ? "Název a cíl jsou převzaté z e-mailového návrhu. Uprav je a doplň další krok i čas kontroly." : "";
    controls(); dialog.showModal(); fields[mode === "reopen" ? "check_at" : "title"].focus();
  }
  function transitions(value) {
    const actions = node("div", undefined, "actions");
    actions.append(button("Hlídání", () => open("reopen", value), value.state === "active"),
      button("Vyřízeno", () => mutate({action: "set_state", id: value.id,
        expected_revision: value.revision, state: "completed"}), value.state === "completed"));
    if (value.state === "active") actions.append(button("Upravit hlídání", () => open("update", value)));
    return actions;
  }
  function paintCard(entry) {
    const value = [...records.values()].find(value => value.source.item_id === entry.item.id
      || Object.hasOwn(value.observations?.items || {}, entry.item.id));
    entry.holder.replaceChildren();
    if (value) {
      entry.holder.append(node("p", `Záležitost: ${value.title}`), transitions(value));
    } else if (["awaiting_confirmation", "archived"].includes(entry.item.status)) {
      entry.holder.append(button("Hlídat tuto záležitost", () => open("create", entry.item)));
    }
    entry.holder.append(node("p", "Archivace nebo skrytí e-mailové karty neukončí evidovanou záležitost.", "meta"));
  }
  function paint() {
    for (const state of ["active", "completed"]) {
      const root = byId(state === "active" ? "followupsActive" : "followupsCompleted");
      root.replaceChildren();
      const values = [...records.values()].filter(value => value.state === state).sort((a, b) => state === "active"
        ? Date.parse(a.check_at) - Date.parse(b.check_at) : Date.parse(b.completed_at) - Date.parse(a.completed_at));
      for (const value of values) {
        const card = node("article", undefined, "card followup-card");
        card.append(node("h3", value.title), node("p", value.goal),
          node("p", `Další krok: ${value.next_step}`), node("p", waitingText[value.waiting_on]),
          node("p", `Zapsaný čas kontroly: ${dateText(value.check_at)} · Praha`, "meta"),
          node("p", value.tracking ? checkText[value.tracking.status] || "Stav kontroly není ověřený."
            : "Automatická kontrola dosud neproběhla.", "meta"), transitions(value));
        if (value.tracking) {
          card.append(node("p", `Poslední kontrola: ${dateText(value.tracking.last_checked_at)}`, "meta"));
          if (value.tracking.last_verified_at) card.append(node("p", `Poslední ověření zdroje: ${dateText(value.tracking.last_verified_at)}`, "meta"));
          if (value.state === "active") card.append(node("p", `Nejdřívější další hodinový slot: ${dateText(value.tracking.next_check_slot)}`, "meta"));
        }
        const detail = node("details"), source = node("div");
        detail.append(node("summary", "Podrobnosti a historie"),
          node("p", `Poslední změna: ${dateText(value.updated_at)}`));
        const showSource = async (itemId = "") => {
          source.textContent = "Načítám uložený zdroj…";
          try {
            const response = await fetch(endpoint + "?id=" + encodeURIComponent(value.id)
              + (itemId ? "&item_id=" + encodeURIComponent(itemId) : ""), {cache: "no-store"});
            const result = await response.json();
            if (!response.ok || !result.ok || result.followup?.id !== value.id) throw new Error();
            const message = result.source_message;
            source.replaceChildren();
            if (!message) { source.textContent = "Uložený zdroj není dostupný nebo neodpovídá původní zprávě."; return; }
            source.append(node("h4", message.header.subject || "(bez předmětu)"),
              node("p", `${message.header.sender} · ${message.header.date}`, "meta"), node("pre", message.body_text));
          } catch (_) { source.textContent = "Uložený zdroj nelze načíst. Záležitost zůstává zachovaná."; }
        };
        detail.append(button("Zobrazit zdrojový e-mail", () => showSource()));
        if (value.state === "active" && value.source.thread_binding !== "verified_headers") {
          detail.append(node("p", "Ověření načte jen přesný původní e-mail, pokud jeho hlavičky nejsou uložené. Nemění schránku.", "meta"),
            button("Ověřit původní e-mail pro párování", () => mutate({action: "verify_source", id: value.id,
              expected_revision: value.revision, confirmed: true})));
        }
        for (const bucket of ["items", "reviews"]) {
          for (const [itemId, event] of Object.entries(value.observations?.[bucket] || {})) {
            detail.append(button(`${bucket === "items" ? "Související zpráva" : "Zpráva k ověření vazby"} · ${dateText(event.observed_at)}`,
              () => showSource(itemId)));
          }
        }
        detail.append(source);
        for (const event of value.history || []) {
          const labels = {source_verified: "Ověření původního e-mailu", related_message: "Příchod související zprávy",
            binding_review: "Vazba zprávy k ověření", monitor_check: "Kontrola hlídání"};
          const label = labels[event.action] || (event.action === "create" ? "Založení" : event.action === "update" ? "Úprava údajů"
            : event.changes?.state === "completed" ? "Vyřízeno" : "Obnovení hlídání");
          detail.append(node("p", `${dateText(event.at || value.updated_at)} · ${label}`, "meta"));
        }
        card.append(detail); root.append(card);
      }
      if (!values.length) root.append(node("p", state === "active" ? "Žádné aktivní záležitosti." : "Žádné vyřízené záležitosti."));
    }
    for (const [id, entry] of cards) {
      if (!document.contains(entry.card)) cards.delete(id);
      else paintCard(entry);
    }
    controls();
  }
  function remember(value) {
    const previous = records.get(value.id);
    if (!previous || value.revision >= previous.revision) records.set(value.id, value);
  }
  function clearPending() {
    window.sessionStorage.removeItem(storageKey);
    pending = null;
  }
  async function read() {
    const response = await fetch(endpoint, {cache: "no-store"});
    const data = await response.json();
    if (!response.ok || !data.ok || !Array.isArray(data.active) || !Array.isArray(data.completed)
        || data.capabilities?.manual_lifecycle !== true || typeof data.capabilities?.automatic_monitoring !== "boolean"
        || data.capabilities.automatic_monitoring && data.capabilities.monitor_version !== 1)
      throw new Error("Ruční evidenci nelze ověřit. Poslední známý přehled zůstává zobrazený.");
    return data;
  }
  async function refresh() {
    if (busy) return;
    const ticket = ++sequence, started = epoch;
    try {
      const data = await read();
      if (ticket !== sequence || started !== epoch) return;
      for (const value of [...data.active, ...data.completed]) remember(value);
      ready = true;
      status.textContent = data.capabilities.automatic_monitoring
        ? "Hodinová kontrola běží. Výsledek a poslední ověření zdroje jsou u každé záležitosti."
        : data.monitor?.configured ? "Hlídání je nastavené, ale běh kontrol není čerstvě ověřený."
        : "Ruční evidence. Automatické sledování odpovědí ani kontrola termínů zatím neběží.";
      if (pending) {
        const found = [...records.values()].find(value =>
          (pending.id ? value.id === pending.id : value.source.item_id === pending.source_item_id)
          && value.history.some(event => event.operation_id === pending.operation_id));
        if (found) {
          clearPending(); dialog.close(); editing = null; epoch++;
          status.textContent += " Původní uložení je ověřené.";
        } else {
          error.textContent = "Výsledek původního uložení není potvrzený. Ověření pouze čte; požadavek znovu neposílej.";
          status.textContent += " Výsledek původního uložení vyžaduje ověření.";
          if (!dialog.open) dialog.showModal();
        }
      }
      if (storageFault) status.textContent = "Úložiště tohoto panelu nelze ověřit. Změny jsou zablokované; přehled lze číst.";
      paint();
    } catch (_) {
      if (ticket !== sequence || started !== epoch) return;
      ready = false;
      status.textContent = "Ruční evidenci nelze ověřit. Poslední známý přehled zůstává zobrazený.";
      if (dialog.open) error.textContent = "Stav nelze ověřit. Rozepsané údaje zůstávají zachované.";
      paint();
    }
  }
  function operationId() {
    const bytes = new Uint8Array(16);
    window.crypto.getRandomValues(bytes);
    return "followup-" + Array.from(bytes, value => value.toString(16).padStart(2, "0")).join("");
  }
  async function mutate(command) {
    if (busy || pending || storageFault || !ready) return;
    const payload = {...command, operation_id: operationId()};
    const intent = {operation_id: payload.operation_id,
      ...(payload.source_item_id ? {source_item_id: payload.source_item_id} : {id: payload.id})};
    try { window.sessionStorage.setItem(storageKey, JSON.stringify(intent)); }
    catch (_) { error.textContent = status.textContent = "Uložení nebylo odesláno: nelze uchovat identitu operace v tomto panelu."; return; }
    pending = intent; busy = true; epoch++; paint();
    try {
      const response = await fetch(endpoint, {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)});
      const result = await response.json();
      if (!response.ok || !result.ok) {
        if ([400, 403, 404, 409].includes(response.status)) {
          clearPending();
          error.textContent = status.textContent = result.message || "Změna nebyla přijata. Zavři formulář, načti aktuální stav a znovu zkontroluj údaje.";
          if (response.status === 409) {
            if (editing) editing.conflict = true;
            error.textContent += " Rozepsané údaje zůstaly zachované; před další úpravou zavři formulář a otevři aktuální záležitost.";
          }
          return;
        }
        throw new Error();
      }
      if (!result.followup?.id) throw new Error();
      remember(result.followup); clearPending();
      dialog.close(); editing = null;
      status.textContent = "Stav záležitosti uložený. Běh automatických kontrol ověřuje přehled.";
    } catch (_) {
      error.textContent = status.textContent = "Výsledek uložení není potvrzený. Použij Ověřit stav; požadavek se automaticky neopakuje.";
      if (!dialog.open) dialog.showModal();
    } finally {
      busy = false; epoch++; paint();
      if (dialog.open) error.scrollIntoView({block: "nearest"});
    }
  }
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (!editing || editing.conflict || busy || pending || storageFault || !ready) return;
    try {
      const current = editing.source, mode = editing.mode;
      const check_at = window.SamanthaFollowupTime.fromInput(fields.check_at.value);
      if ((mode !== "update" || Date.parse(check_at) !== Date.parse(current.check_at)) && Date.parse(check_at) <= Date.now())
        throw new Error("Zvol nový čas kontroly v budoucnosti.");
      if (mode === "reopen") {
        await mutate({action: "set_state", id: current.id, expected_revision: current.revision,
          state: "active", check_at});
      } else {
        const values = {title: fields.title.value.trim(), goal: fields.goal.value.trim(),
          next_step: fields.next_step.value.trim(), waiting_on: fields.waiting_on.value, check_at};
        if (!values.title || !values.goal || !values.next_step) throw new Error("Doplň název, cíl a další krok.");
        if (mode === "update" && Object.keys(values).every(key => key === "check_at"
          ? Date.parse(values[key]) === Date.parse(current[key]) : values[key] === current[key])) { close(); return; }
        await mutate(mode === "create" ? {action: "create", source_item_id: current.id, fields: values}
          : {action: "update", id: current.id, expected_revision: current.revision, fields: values});
      }
    } catch (exc) { error.textContent = exc.message; error.scrollIntoView({block: "nearest"}); }
  });
  byId("followupCancel").addEventListener("click", close);
  dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
  byId("followupVerify").addEventListener("click", refresh);
  window.SamanthaEmailFollowups = {
    refresh, isOpen: () => dialog.open || busy,
    attach(card, item) {
      const holder = node("section", undefined, "followup-controls");
      const entry = {card, item, holder}; card.append(holder); cards.set(item.id, entry); paintCard(entry);
    },
    syncCards: paint,
  };
  controls();
})();
