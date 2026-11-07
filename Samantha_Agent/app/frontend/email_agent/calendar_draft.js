(() => {
  const endpoint = "/api/email-agent/calendar-draft";
  const fieldKeys = ["kind", "title", "date", "start_time", "end_date", "end_time", "duration_minutes", "time_zone", "location", "join_url", "all_day"];
  const fieldLabels = {kind: "Typ", title: "Název", date: "Datum", start_time: "Čas začátku", end_date: "Datum konce", end_time: "Čas konce", duration_minutes: "Délka v minutách", time_zone: "Časové pásmo", location: "Místo", join_url: "Odkaz na připojení", all_day: "Celý den"};
  const kinds = [["meeting", "Schůzka"], ["task_deadline", "Termín úkolu"], ["manual_required", "Vyžaduje ruční zpracování"], ["not_applicable", "Nevztahuje se"]];
  let dialog, elements = {}, item, generation = 0, loadVersion = 0, timer = null, polls = 0, busy = false, dirty = false, loadedDraft = null, prepareLocked = false;

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function button(label, handler, secondary = false) {
    const b = el("button", label, secondary ? "secondary" : "");
    b.type = "button";
    b.addEventListener("click", handler);
    return b;
  }
  function makeField(key, type = "text") {
    const label = el("label", fieldLabels[key]);
    let input;
    if (key === "kind") {
      input = document.createElement("select");
      for (const [value, text] of kinds) {
        const option = el("option", text);
        option.value = value;
        input.append(option);
      }
    } else {
      input = document.createElement("input");
      input.type = type;
      if (key === "duration_minutes") input.min = "1";
      if (key === "time_zone") input.placeholder = "Europe/Prague";
      if (key === "join_url") input.inputMode = "url";
      if (key === "all_day") input.type = "checkbox";
    }
    input.id = `calendarDraft_${key}`;
    input.addEventListener("input", markDirty);
    input.addEventListener("change", markDirty);
    label.append(input);
    elements[key] = input;
    return label;
  }
  function createDialog() {
    dialog = document.createElement("dialog");
    dialog.id = "calendarDraftEditor";
    const form = document.createElement("form");
    form.addEventListener("submit", event => event.preventDefault());
    form.append(el("h2", "Návrh do kalendáře"));
    elements.subject = el("p");
    form.append(elements.subject);
    elements.status = el("p");
    elements.status.setAttribute("role", "status");
    elements.status.setAttribute("aria-live", "polite");
    form.append(elements.status);
    elements.notice = el("p", "Pouze návrh. Kontrola kolizí a zápis do kalendáře přijdou později.");
    form.append(elements.notice);
    elements.disclosure = el("p");
    form.append(elements.disclosure);
    elements.quotes = el("section");
    form.append(elements.quotes);
    elements.issues = el("section");
    form.append(elements.issues);
    const fields = document.createElement("section");
    fields.append(makeField("kind"), makeField("title"), makeField("date", "date"), makeField("start_time", "time"), makeField("end_date", "date"), makeField("end_time", "time"), makeField("duration_minutes", "number"), makeField("time_zone"), makeField("location"), makeField("join_url", "url"), makeField("all_day"));
    form.append(fields);
    form.append(el("p", "U typu Termín úkolu znamená Čas začátku nejzazší čas splnění; konec ani délku nevyplňuj."));
    const actions = el("div", undefined, "actions");
    elements.prepare = button("Připravit návrh modelem", prepare);
    elements.save = button("Uložit návrh", save);
    elements.refresh = button("Obnovit stav", refreshState, true);
    elements.close = button("Zavřít", close, true);
    actions.append(elements.prepare, elements.save, elements.refresh, elements.close);
    form.append(actions);
    dialog.append(form);
    dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
    dialog.addEventListener("click", event => { if (event.target === dialog) close(); });
    dialog.addEventListener("close", stopPolling);
    document.body.append(dialog);
  }
  function markDirty() {
    if (busy) return;
    dirty = true;
    syncControls();
  }
  function syncControls() {
    if (!dialog) return;
    for (const key of fieldKeys) elements[key].disabled = busy || !loadedDraft;
    elements.close.disabled = busy;
    elements.save.disabled = busy || !loadedDraft;
    elements.prepare.disabled = busy || !item || Boolean(loadedDraft) || prepareLocked || elements.prepare.dataset.job === "present";
    elements.refresh.disabled = busy || !item;
  }
  function setFields(fields) {
    for (const key of fieldKeys) {
      const value = fields && fields[key];
      if (key === "all_day") elements[key].checked = value === true;
      else elements[key].value = value == null ? "" : String(value);
    }
  }
  function readFields() {
    const fields = {};
    for (const key of fieldKeys) fields[key] = key === "all_day" ? elements[key].checked : elements[key].value;
    return fields;
  }
  function showList(container, heading, values) {
    container.replaceChildren();
    if (!values || !values.length) return;
    container.append(el("h3", heading));
    const list = document.createElement("ul");
    for (const value of values) list.append(el("li", value));
    container.append(list);
  }
  function showQuotes(evidence) {
    elements.quotes.replaceChildren();
    const rows = Object.entries(evidence || {});
    if (!rows.length) return;
    elements.quotes.append(el("h3", "Citace ze zdroje"));
    for (const [key, entry] of rows) {
      const section = document.createElement("section");
      section.append(el("h4", fieldLabels[key] || key));
      if (entry && entry.quote) section.append(el("blockquote", entry.quote));
      const origin = entry && entry.origin;
      if (origin) section.append(el("p", `Původ: ${({user: "uživatel", email_quote: "citace z e-mailu", inferred: "odvozeno", missing: "chybí"})[origin] || origin}`));
      if (entry && entry.source) section.append(el("p", `Zdroj: ${entry.source}`));
      elements.quotes.append(section);
    }
    elements.quotes.append(el("p", "Citace samy o sobě nepotvrzují normalizovanou hodnotu návrhu."));
  }
  function update(data, initial = false) {
    if (data.source) elements.subject.textContent = `Zdrojový e-mail: ${data.source.subject || "(bez předmětu)"}${data.source.date ? ` · ${data.source.date}` : ""}`;
    const draft = data.draft || null;
    if (draft) {
      if (initial || !dirty) setFields(draft.fields || {});
      if (initial || !dirty) loadedDraft = draft;
      else if (loadedDraft) loadedDraft = {...loadedDraft, revision: loadedDraft.revision};
      showQuotes(draft.evidence);
      showList(elements.issues, "Upozornění", draft.issues || []);
      elements.status.textContent = `Návrh uložen (revize ${draft.revision}).${draft.normalized ? " Byly vypočteny normalizované časy." : ""}`;
    } else {
      if (initial) { setFields({}); loadedDraft = null; }
      showQuotes(null);
      showList(elements.issues, "Upozornění", []);
      elements.status.textContent = "Zatím není připravený návrh.";
    }
    const job = data.job;
    const active = job && ["queued", "running"].includes(job.status);
    elements.prepare.dataset.job = job ? "present" : "";
    elements.prepare.hidden = Boolean(draft || job);
    if (!job && !busy) prepareLocked = false;
    elements.disclosure.textContent = !draft && !job ? `Po potvrzení bude schválenému modelu ${data.model || "e-mailového agenta"} odeslán pouze tento vybraný e-mail.` : "";
    if (job && ["failed", "delivery_unknown"].includes(job.status)) elements.status.textContent = job.message || "Výsledek vyžaduje ověření. Nový modelový pokus nespouštěj.";
    if (active) {
      elements.status.textContent = "Příprava návrhu probíhá…";
      if (!dirty) schedulePoll();
    } else stopPolling();
    syncControls();
  }
  async function getState(token, initial = false) {
    const version = ++loadVersion;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 35000);
    try {
      const response = await fetch(`${endpoint}?id=${encodeURIComponent(item.id)}`, {cache: "no-store", signal: controller.signal});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Stav návrhu se nepodařilo načíst.");
      if (token === generation && version === loadVersion && !busy && dialog.open) update(data, initial);
      return data;
    } finally { clearTimeout(timeout); }
  }
  function errorText(error) { return error && error.name === "AbortError" ? "Požadavek trval příliš dlouho. Obnov stav ručně; operace se automaticky neopakuje." : (error.message || "Požadavek se nepodařilo dokončit."); }
  async function refreshState() {
    if (busy) return;
    stopPolling();
    const token = generation;
    elements.status.textContent = "Načítám stav…";
    try { await getState(token); }
    catch (error) { if (token === generation) elements.status.textContent = errorText(error); }
  }
  function schedulePoll() {
    if (timer || polls >= 180 || !dialog.open) return;
    timer = setTimeout(async () => {
      timer = null;
      if (!dialog.open) return;
      const token = generation;
      polls++;
      try {
        const data = await getState(token);
        if (token === generation && data.job && ["queued", "running"].includes(data.job.status) && polls < 180) schedulePoll();
        else if (token === generation && polls >= 180) elements.status.textContent = "Automatické kontroly skončily. Stav můžeš obnovit ručně.";
      } catch (error) { if (token === generation) elements.status.textContent = `${errorText(error)} Obnov stav ručně.`; }
    }, 1000);
  }
  function stopPolling() { if (timer) clearTimeout(timer); timer = null; }
  async function post(payload) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 35000);
    try {
      const response = await fetch(endpoint, {method: "POST", cache: "no-store", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload), signal: controller.signal});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Požadavek se nepodařilo dokončit.");
      return data;
    } finally { clearTimeout(timeout); }
  }
  async function prepare() {
    if (busy || loadedDraft || !item || prepareLocked || elements.prepare.dataset.job === "present") return;
    stopPolling();
    busy = true; prepareLocked = true; loadVersion++; syncControls();
    const token = generation;
    elements.status.textContent = "Odesílám požadavek na přípravu návrhu…";
    try {
      const data = await post({action: "prepare", id: item.id, request_id: crypto.randomUUID(), expected_content_digest: item.content_digest, confirmed: true});
      if (token === generation && dialog.open) update(data, true);
    } catch (error) {
      if (token === generation) elements.status.textContent = `${errorText(error)} Požadavek znovu neposílej; můžeš ručně obnovit stav.`;
    } finally { if (token === generation) { busy = false; syncControls(); } }
  }
  async function save() {
    if (busy || !loadedDraft) return;
    busy = true; loadVersion++; syncControls();
    const token = generation;
    elements.status.textContent = "Ukládám návrh…";
    try {
      const data = await post({action: "save", id: item.id, expected_revision: loadedDraft.revision, fields: readFields()});
      if (token === generation && dialog.open) { dirty = false; update(data, true); }
    } catch (error) {
      if (token === generation) elements.status.textContent = `${errorText(error)} Zadané hodnoty zůstaly zachované; stav můžeš obnovit ručně.`;
    } finally { if (token === generation) { busy = false; syncControls(); } }
  }
  function close() {
    if (busy) return;
    if (dirty && !window.confirm("Zahodit neuložené změny návrhu?")) return;
    stopPolling(); generation++;
    dialog.close();
    dirty = false; loadedDraft = null; item = null;
  }
  async function open(selectedItem) {
    if (busy) return;
    if (!dialog) createDialog();
    if (dialog.open && dirty && !window.confirm("Zahodit neuložené změny návrhu a otevřít jiný e-mail?")) return;
    stopPolling();
    generation++; const token = generation;
    polls = 0; busy = false; dirty = false; loadedDraft = null; prepareLocked = true; item = selectedItem;
    elements.prepare.dataset.job = "";
    elements.subject.textContent = `Zdrojový e-mail: ${(selectedItem.header || {}).subject || "(bez předmětu)"}`;
    elements.status.textContent = "Načítám stav návrhu…";
    elements.disclosure.textContent = "";
    setFields({}); showQuotes(null); showList(elements.issues, "Upozornění", []);
    if (!dialog.open) dialog.showModal();
    syncControls();
    try { await getState(token, true); }
    catch (error) { if (token === generation) elements.status.textContent = errorText(error); }
  }
  window.SamanthaCalendarDraft = {open, isOpen: () => Boolean(dialog && dialog.open)};
})();
