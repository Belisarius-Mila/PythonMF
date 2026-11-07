(() => {
  const endpoint = "/api/email-agent/calendar-draft";
  const fieldKeys = ["kind", "title", "date", "start_time", "end_date", "end_time", "duration_minutes", "time_zone", "location", "join_url", "all_day"];
  const fieldLabels = {kind: "Typ", title: "Název", date: "Datum", start_time: "Čas začátku", end_date: "Datum konce", end_time: "Čas konce", duration_minutes: "Délka v minutách", time_zone: "Časové pásmo", location: "Místo", join_url: "Odkaz na připojení", all_day: "Celý den"};
  const kinds = [["meeting", "Schůzka"], ["task_deadline", "Termín úkolu"], ["manual_required", "Vyžaduje ruční zpracování"], ["not_applicable", "Nevztahuje se"]];
  let dialog, elements = {}, item, generation = 0, loadVersion = 0, timer = null, polls = 0, busy = false, dirty = false, loadedDraft = null, prepareLocked = false;
  let automaticEnd = true, review = null, confirmedReview = null, reviewTimer = null;

  function localInstant(day, time, zone) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) return null;
    const naive = Date.parse(`${day}T${time}:00Z`);
    if (!Number.isFinite(naive) || new Date(naive).toISOString().slice(0,16) !== `${day}T${time}`) return null;
    try {
      const format = new Intl.DateTimeFormat("en-CA", {timeZone: zone, year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", hourCycle:"h23"});
      const wall = value => {
        const p = Object.fromEntries(format.formatToParts(new Date(value)).map(part => [part.type, part.value]));
        return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
      };
      const offsets = new Set();
      for (let hour = -36; hour <= 36; hour += 6) {
        const sample = naive + hour*3600000;
        offsets.add(Date.parse(wall(sample)+":00Z")-sample);
      }
      const choices = [...offsets].map(offset => naive-offset).filter(value => wall(value) === `${day}T${time}`);
      return choices.length === 1 ? choices[0] : null;
    } catch { return null; }
  }
  function defaultEnd() {
    const value = elements.date.value;
    if (!elements.all_day.checked) {
      const duration=elements.duration_minutes.value;
      if (!elements.end_time.value && /^[1-9]\d{0,4}$/.test(duration) && Number(duration)<=10080) {
        const start=localInstant(value,elements.start_time.value,elements.time_zone.value);
        if (start !== null) {
          const parts=Object.fromEntries(new Intl.DateTimeFormat("en-CA",{timeZone:elements.time_zone.value,year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date(start+Number(duration)*60000)).map(part=>[part.type,part.value]));
          return `${parts.year}-${parts.month}-${parts.day}`;
        }
      }
      return value;
    }
    const day = new Date(`${value}T12:00:00Z`);
    if (!Number.isFinite(day.getTime())) return "";
    day.setUTCDate(day.getUTCDate()+1);
    return day.toISOString().slice(0,10);
  }
  function calculate(changed) {
    if (changed === "end_date") automaticEnd = !elements.end_date.value;
    if (elements.kind.value !== "meeting") return;
    if (automaticEnd || !elements.end_date.value) elements.end_date.value = defaultEnd();
    if (elements.end_time.value && !elements.all_day.checked) {
      const a = localInstant(elements.date.value, elements.start_time.value, elements.time_zone.value);
      const b = localInstant(elements.end_date.value, elements.end_time.value, elements.time_zone.value);
      elements.duration_minutes.value = a !== null && b !== null && b > a && b-a <= 10080*60000 ? String((b-a)/60000) : "";
    }
  }

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
    input.addEventListener("input", () => markDirty(key));
    input.addEventListener("change", () => markDirty(key));
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
    elements.notice = el("p", "Pouze návrh. Kolize lze zkontrolovat před potvrzením; zápis události ještě není zapnutý.");
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
    form.append(el("p", "Datum konce se doplní podle začátku; u celodenní události je konec následující, nezahrnutý den. Délka se počítá z obou časů v uvedeném pásmu."));
    const reminders = el("fieldset");
    reminders.append(el("legend", "Upozornění před začátkem / termínem"));
    for (const [minutes, label] of [[1440,"1 den předem (24 hodin)"],[60,"1 hodinu předem"]]) {
      const row = el("label", label), input = el("input");
      input.type = "checkbox"; input.checked = true; input.id = `calendarReminder${minutes}`;
      input.addEventListener("change", () => markDirty()); row.append(input); reminders.append(row); elements[`reminder${minutes}`] = input;
    }
    form.append(reminders);
    form.append(el("p", "U celodenní události se upozornění počítají od půlnoci jejího začátku. Náhled ukáže přesné časy. Upozornění začnou fungovat až se skutečně uloženou událostí v další etapě."));
    elements.preview = el("section", undefined, "calendar-final-preview"); form.append(elements.preview);
    elements.ack = el("input"); elements.ack.type="checkbox"; elements.ack.id="calendarReviewAcknowledged";
    elements.accept = el("input"); elements.accept.type="checkbox"; elements.accept.id="calendarConflictsAccepted";
    for (const input of [elements.ack,elements.accept]) input.addEventListener("change", syncControls);
    elements.ackLabel=el("label","Zkontroloval jsem údaje, citace a případné nejasnosti."); elements.ackLabel.append(elements.ack);
    elements.acceptLabel=el("label","Přijímám zobrazené časové kolize."); elements.acceptLabel.append(elements.accept);
    form.append(elements.ackLabel,elements.acceptLabel);
    const actions = el("div", undefined, "actions");
    elements.prepare = button("Připravit návrh modelem", prepare);
    elements.save = button("Uložit návrh", save);
    elements.refresh = button("Obnovit stav", refreshState, true);
    elements.close = button("Zavřít", close, true);
    elements.review = button("Zkontrolovat kolize a zobrazit náhled", () => reviewAction(false));
    elements.confirm = button("Potvrdit návrh", () => reviewAction(true));
    actions.append(elements.prepare, elements.save, elements.review, elements.confirm, elements.refresh, elements.close);
    form.append(actions);
    dialog.append(form);
    dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
    dialog.addEventListener("click", event => { if (event.target === dialog) close(); });
    dialog.addEventListener("close", stopPolling);
    document.body.append(dialog);
  }
  function markDirty(key) {
    if (busy) return;
    dirty = true;
    calculate(key); review = null; confirmedReview = null;
    showReview();
    syncControls();
  }
  function syncControls() {
    if (!dialog) return;
    for (const key of fieldKeys) elements[key].disabled = busy || !loadedDraft;
    elements.close.disabled = busy;
    elements.save.disabled = busy || !loadedDraft;
    elements.prepare.disabled = busy || !item || Boolean(loadedDraft) || prepareLocked || elements.prepare.dataset.job === "present";
    elements.refresh.disabled = busy || !item;
    for (const minutes of [1440,60]) elements[`reminder${minutes}`].disabled = busy || !loadedDraft;
    elements.duration_minutes.readOnly = Boolean(elements.end_time.value && !elements.all_day.checked && elements.kind.value === "meeting");
    elements.review.disabled = busy || !loadedDraft || dirty;
    elements.confirm.disabled = busy || dirty || !review || !review.valid || Boolean(confirmedReview) || !elements.ack.checked || (review.conflicts.length > 0 && !elements.accept.checked);
    elements.ack.disabled = busy || !review || !review.valid;
    elements.accept.disabled = busy || !review || !review.valid;
  }
  function setFields(fields, evidence) {
    for (const key of fieldKeys) {
      const value = fields && fields[key];
      if (key === "all_day") elements[key].checked = value === true;
      else elements[key].value = value == null ? "" : String(value);
    }
    automaticEnd = evidence?.end_date?.origin === "calculated" || !fields || !fields.end_date || fields.end_date === fields.date || (fields.all_day && fields.end_date === defaultEnd());
    calculate();
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
      if (origin) section.append(el("p", `Původ: ${({user: "uživatel", email_quote: "citace z e-mailu", inferred: "odvozeno", calculated: "automatický výpočet / výchozí datum", missing: "chybí"})[origin] || origin}`));
      if (entry && entry.source) section.append(el("p", `Zdroj: ${entry.source}`));
      elements.quotes.append(section);
    }
    elements.quotes.append(el("p", "Citace samy o sobě nepotvrzují normalizovanou hodnotu návrhu."));
  }
  function update(data, initial = false) {
    if (data.source) elements.subject.textContent = `Zdrojový e-mail: ${data.source.subject || "(bez předmětu)"}${data.source.date ? ` · ${data.source.date}` : ""}`;
    const draft = data.draft || null;
    if (draft) {
      if (initial || !dirty) {
        setFields(draft.fields || {}, draft.evidence);
        for (const minutes of [1440,60]) elements[`reminder${minutes}`].checked = (draft.reminders || [1440,60]).includes(minutes);
      }
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
    if (!dirty) { review = data.review || null; confirmedReview = data.confirmation || null; showReview(); }
    if (data.message) elements.status.textContent = data.message;
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
      const data = await post({action: "save", id: item.id, expected_revision: loadedDraft.revision, fields: readFields(), reminders: [1440,60].filter(minutes => elements[`reminder${minutes}`].checked)});
      if (token === generation && dialog.open) { dirty = false; update(data, true); }
    } catch (error) {
      if (token === generation) elements.status.textContent = `${errorText(error)} Zadané hodnoty zůstaly zachované; stav můžeš obnovit ručně.`;
    } finally { if (token === generation) { busy = false; syncControls(); } }
  }
  function showReview() {
    if (reviewTimer) { clearTimeout(reviewTimer); reviewTimer=null; }
    elements.preview.replaceChildren(); elements.ack.checked=false; elements.accept.checked=false;
    elements.ackLabel.hidden = !review; elements.acceptLabel.hidden = !review || !review.conflicts.length;
    if (!review) return;
    if (review.valid && review.expires_at) reviewTimer=setTimeout(() => {
      reviewTimer=null; if (review) review={...review,valid:false}; confirmedReview=null; showReview(); syncControls();
    },Math.max(0,Date.parse(review.expires_at)-Date.now()));
    elements.preview.append(el("h3", confirmedReview ? "Návrh potvrzený · událost ještě není zapsaná" : "Konečný náhled"));
    if (!review.valid) elements.preview.append(el("p","Náhled už není aktuální. Zkontroluj kolize znovu."));
    const f=review.fields;
    const format = value => { try { return new Intl.DateTimeFormat("cs-CZ",{timeZone:f.time_zone,dateStyle:"medium",timeStyle:"short"}).format(new Date(value)); } catch { return value; } };
    elements.preview.append(el("p",f.title));
    elements.preview.append(el("p",review.deadline_is_point ? `Termín: ${format(review.normalized.deadline)} · ${f.time_zone}` : `${format(review.normalized.start)} – ${format(review.normalized.end)} · ${f.time_zone}${f.all_day ? " · celý den, konec je nezahrnutý" : ""}`));
    elements.preview.append(el("p", `Typ: ${kinds.find(([key]) => key===f.kind)?.[1] || f.kind} · Cílový kalendář: ${review.target.title} · ${review.target.source_title}`));
    if (f.location || f.join_url) elements.preview.append(el("p", `${f.location} ${f.join_url}`));
    elements.preview.append(el("p", `Kontrolované kalendáře: ${review.read_calendars.map(row=>row.title).join(", ")}`));
    showList(appendSection(elements.preview), "Upozornění události", review.alerts.map(row=>`${row.minutes_before===1440 ? "1 den" : "1 hodinu"} předem: ${format(row.at)}${row.past ? " (čas už uplynul)" : ""}`));
    if (!review.alerts.length) elements.preview.append(el("p","Upozornění události: vypnutá."));
    for (const conflict of review.conflicts) elements.preview.append(el("p",`Kolize: ${conflict.title} · ${format(conflict.start)} – ${format(conflict.end)} · ${conflict.calendar_title}`));
    if (!review.conflicts.length) elements.preview.append(el("p",review.deadline_is_point ? "V okamžiku termínu není překryv; termín se nepovažuje za dobu schůzky." : "Ve vybraných kalendářích nebyl nalezen překryv."));
    elements.preview.append(el("p",`Poslední kontrola: ${format(review.observed_at)}. Náhled platí 5 minut. Potvrzení znovu načte kalendáře; souběžné změny na jiném zařízení nelze zamknout.`));
  }
  function appendSection(parent) { const section=el("section"); parent.append(section); return section; }
  async function reviewAction(confirming) {
    if (busy || dirty || !loadedDraft || (confirming && (!review || !review.valid || !elements.ack.checked || (review.conflicts.length && !elements.accept.checked)))) return;
    busy=true; loadVersion++; stopPolling(); syncControls(); const token=generation;
    elements.status.textContent="Načítám aktuální kalendáře…";
    const payload={action:confirming ? "confirm" : "review",id:item.id,expected_revision:loadedDraft.revision,
      ...(confirming ? {review_id:review.review_id,acknowledged:true,accept_conflicts:elements.accept.checked} : {confirmed:true})};
    try { const data=await post(payload); if(token===generation && dialog.open) update(data,true); }
    catch(error) { if(token===generation) { elements.status.textContent=errorText(error); confirmedReview=null; if(review) review={...review,valid:false}; showReview(); } }
    finally { if(token===generation) {busy=false;syncControls();} }
  }
  function close() {
    if (busy) return;
    if (dirty && !window.confirm("Zahodit neuložené změny návrhu?")) return;
    stopPolling(); generation++;
    if (reviewTimer) { clearTimeout(reviewTimer); reviewTimer=null; }
    dialog.close();
    dirty = false; loadedDraft = null; item = null; review=null; confirmedReview=null;
  }
  async function open(selectedItem) {
    if (busy) return;
    if (!dialog) createDialog();
    if (dialog.open && dirty && !window.confirm("Zahodit neuložené změny návrhu a otevřít jiný e-mail?")) return;
    stopPolling();
    generation++; const token = generation;
    polls = 0; busy = false; dirty = false; loadedDraft = null; prepareLocked = true; item = selectedItem; review=null; confirmedReview=null;
    elements.prepare.dataset.job = "";
    elements.subject.textContent = `Zdrojový e-mail: ${(selectedItem.header || {}).subject || "(bez předmětu)"}`;
    elements.status.textContent = "Načítám stav návrhu…";
    elements.disclosure.textContent = "";
    setFields({}); showQuotes(null); showList(elements.issues, "Upozornění", []);
    showReview();
    if (!dialog.open) dialog.showModal();
    syncControls();
    try { await getState(token, true); }
    catch (error) { if (token === generation) elements.status.textContent = errorText(error); }
  }
  window.SamanthaCalendarDraft = {open, isOpen: () => Boolean(dialog && dialog.open)};
})();
